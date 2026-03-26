# skill: proxmox-create
version: 2.0
description: >
  Sei un esperto Proxmox VE. Usi la libreria Python **proxmoxer** come metodo
  principale per interagire con l'API Proxmox. Sai anche generare chiamate
  REST dirette (curl/fetch JS) e comandi pvesh come alternativa.
  Genera sempre codice funzionante, con parametri corretti e gestione dei task asincroni.
  Preferisci autenticazione via API Token. Rispondi in italiano se richiesto.
  Riferimento API ufficiale: https://pve.proxmox.com/pve-docs/api-viewer/
  Documentazione proxmoxer: https://proxmoxer.github.io/docs/

---

## installazione

```bash
pip install proxmoxer requests
# backend SSH (opzionale)
pip install paramiko
```

---

## connessione

### Con password
```python
from proxmoxer import ProxmoxAPI

proxmox = ProxmoxAPI(
    "pve-host",
    user="root@pam",
    password="secret",
    verify_ssl=False  # rimuovere se si usa un cert valido
)
```

### Con API Token (raccomandato per script e web app)
```python
from proxmoxer import ProxmoxAPI

proxmox = ProxmoxAPI(
    "pve-host",
    user="root@pam",
    token_name="mytoken",
    token_value="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    verify_ssl=False
)
```

### Via SSH (senza HTTP, utile per automazione interna)
```python
proxmox = ProxmoxAPI("pve-host", user="root", backend="openssh")
```

---

## notazione: dotted vs string

Proxmoxer supporta due stili equivalenti — si possono combinare:

```python
# Dotted notation (più pythonica)
proxmox.nodes("pve").lxc.get()

# String notation (più flessibile)
proxmox("nodes/pve/lxc").get()

# Equivalenti completi dello stesso endpoint
proxmox.nodes("pve").lxc.get()
proxmox.nodes("pve").get("lxc")
proxmox.get("nodes/pve/lxc")
proxmox.get("nodes", "pve", "lxc")

# Endpoint con trattino (usa string notation per quella sezione)
proxmox.nodes("pve").qemu("100").agent("exec-status").get(pid=1234)
```

---

## helper base

```python
import time
from proxmoxer import ProxmoxAPI

proxmox = ProxmoxAPI(
    "pve-host",
    user="root@pam",
    token_name="mytoken",
    token_value="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    verify_ssl=False
)

def next_vmid():
    """Restituisce il prossimo VMID libero nel cluster."""
    return int(proxmox.cluster.nextid.get())

def wait_task(node: str, upid: str, interval: int = 2) -> dict:
    """Attende il completamento di un task asincrono (UPID)."""
    while True:
        status = proxmox.nodes(node).tasks(upid).status.get()
        if status["status"] == "stopped":
            if status.get("exitstatus") != "OK":
                raise RuntimeError(f"Task fallito: {status.get('exitstatus')}")
            return status
        time.sleep(interval)
```

---

## CREARE UN CONTAINER LXC

### Parametri obbligatori
| Parametro    | Tipo   | Descrizione                                                    |
|--------------|--------|----------------------------------------------------------------|
| `vmid`       | int    | ID univoco (usa `next_vmid()`)                                 |
| `ostemplate` | string | Es: `local:vztmpl/debian-12-standard_12.0-1_amd64.tar.zst`    |
| `storage`    | string | Storage per il root disk: `local-lvm`, `local`, ecc.          |

### Parametri comuni opzionali
| Parametro        | Default | Descrizione                                                |
|------------------|---------|------------------------------------------------------------|
| `hostname`       | —       | Hostname del container                                     |
| `password`       | —       | Password root                                              |
| `cores`          | 1       | CPU cores                                                  |
| `memory`         | 512     | RAM in MB                                                  |
| `swap`           | 512     | Swap in MB                                                 |
| `rootfs`         | —       | `local-lvm:8` — storage:dimensione GB                      |
| `net0`           | —       | `name=eth0,bridge=vmbr0,ip=dhcp`                           |
| `unprivileged`   | 0       | `1` = container non privilegiato (raccomandato)            |
| `start`          | 0       | `1` = avvia subito dopo la creazione                       |
| `onboot`         | 0       | `1` = avvia al boot del nodo                               |
| `nameserver`     | —       | DNS server IP                                              |
| `searchdomain`   | —       | Dominio DNS di ricerca                                     |
| `ssh-public-keys`| —       | Chiave SSH pubblica                                        |
| `features`       | —       | `nesting=1,keyctl=1` (per Docker dentro LXC)               |
| `description`    | —       | Testo descrittivo                                          |
| `tags`           | —       | Tag separati da `;`                                        |

### Esempio base
```python
vmid = next_vmid()
node = proxmox.nodes("pve")

upid = node.lxc.create(
    vmid=vmid,
    hostname="web-server-01",
    ostemplate="local:vztmpl/debian-12-standard_12.0-1_amd64.tar.zst",
    storage="local-lvm",
    rootfs="local-lvm:8",
    cores=2,
    memory=1024,
    swap=512,
    password="SecurePass123!",
    net0="name=eth0,bridge=vmbr0,ip=dhcp,firewall=1",
    unprivileged=1,
    start=1,
    onboot=1,
    description="Web server creato con proxmoxer",
)

wait_task("pve", upid)
print(f"Container {vmid} creato con successo")
```

### Esempio con parametri come dizionario (utile per ssh-public-keys)
```python
config = {
    "vmid":         next_vmid(),
    "hostname":     "dev-container",
    "ostemplate":   "local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst",
    "storage":      "local-lvm",
    "rootfs":       "local-lvm:16",
    "cores":        4,
    "memory":       2048,
    "swap":         1024,
    "password":     "DevPass456!",
    "net0":         "name=eth0,bridge=vmbr0,ip=192.168.1.50/24,gw=192.168.1.1",
    "unprivileged": 1,
    "onboot":       1,
    "features":     "nesting=1",
    "ssh-public-keys": "ssh-ed25519 AAAA... user@host",
}

upid = proxmox.nodes("pve").lxc.create(**config)
wait_task("pve", upid)
```

### pvesh equivalente
```bash
pvesh create /nodes/pve/lxc \
  --vmid 200 --hostname web-server-01 \
  --ostemplate local:vztmpl/debian-12-standard_12.0-1_amd64.tar.zst \
  --storage local-lvm --rootfs local-lvm:8 \
  --cores 2 --memory 1024 --swap 512 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --unprivileged 1 --start 1
```

---

## CREARE UNA VM QEMU/KVM

### Parametri obbligatori
| Parametro | Tipo | Descrizione                   |
|-----------|------|-------------------------------|
| `vmid`    | int  | ID univoco (usa `next_vmid()`) |

### Parametri comuni opzionali
| Parametro     | Default   | Descrizione                                                      |
|---------------|-----------|------------------------------------------------------------------|
| `name`        | —         | Nome della VM                                                    |
| `cores`       | 1         | CPU cores                                                        |
| `sockets`     | 1         | Socket CPU                                                       |
| `cpu`         | `kvm64`   | Tipo CPU: `host`, `kvm64`, `x86-64-v2-AES`                       |
| `memory`      | 512       | RAM in MB                                                        |
| `balloon`     | —         | RAM minima balloon (`0` = disabilita)                            |
| `ostype`      | —         | `l26` (Linux), `win11`, `win10`, `other`                         |
| `boot`        | —         | `order=scsi0;ide2;net0`                                          |
| `scsi0`       | —         | `local-lvm:32,cache=writeback,discard=on`                        |
| `ide2`        | —         | `local:iso/ubuntu-22.04.iso,media=cdrom`                         |
| `net0`        | —         | `virtio,bridge=vmbr0,firewall=1`                                 |
| `scsihw`      | —         | `virtio-scsi-pci` (raccomandato)                                 |
| `vga`         | `std`     | `serial0`, `virtio`, `std`                                       |
| `agent`       | —         | `enabled=1` (QEMU guest agent)                                   |
| `bios`        | `seabios` | `seabios` o `ovmf` (UEFI)                                        |
| `machine`     | —         | `q35` (raccomandato per Windows/UEFI)                            |
| `efidisk0`    | —         | `local-lvm:1` — richiesto con UEFI/OVMF                          |
| `onboot`      | 0         | `1` = avvia al boot del nodo                                     |
| `start`       | 0         | `1` = avvia subito dopo la creazione                             |
| `description` | —         | Testo descrittivo                                                |
| `tags`        | —         | Tag separati da `;`                                              |
| `ciuser`      | —         | Cloud-Init: username                                             |
| `cipassword`  | —         | Cloud-Init: password                                             |
| `sshkeys`     | —         | Cloud-Init: chiavi SSH (urlencode)                               |
| `ipconfig0`   | —         | Cloud-Init: `ip=192.168.1.10/24,gw=192.168.1.1` o `ip=dhcp`     |

### Esempio — VM Linux con ISO
```python
vmid = next_vmid()

upid = proxmox.nodes("pve").qemu.create(
    vmid=vmid,
    name="ubuntu-server-01",
    ostype="l26",
    cores=2,
    memory=2048,
    balloon=0,
    cpu="host",
    scsihw="virtio-scsi-pci",
    scsi0="local-lvm:32,cache=writeback,discard=on",
    ide2="local:iso/ubuntu-22.04.3-live-server-amd64.iso,media=cdrom",
    net0="virtio,bridge=vmbr0,firewall=1",
    boot="order=scsi0;ide2",
    vga="std",
    agent="enabled=1",
    onboot=1,
    description="Ubuntu server creato con proxmoxer",
)

wait_task("pve", upid)
print(f"VM {vmid} creata con successo")
```

### Esempio — VM con Cloud-Init
```python
vmid = next_vmid()
node = proxmox.nodes("pve")

# Crea la VM
upid = node.qemu.create(
    vmid=vmid,
    name="ubuntu-cloud-01",
    ostype="l26",
    cores=2,
    memory=2048,
    scsihw="virtio-scsi-pci",
    scsi0="local-lvm:32,cache=writeback,discard=on",
    ide2="local-lvm:cloudinit",
    net0="virtio,bridge=vmbr0",
    boot="order=scsi0",
    agent="enabled=1",
    ciuser="admin",
    cipassword="ChangeMe!",
    ipconfig0="ip=dhcp",
    onboot=1,
)
wait_task("pve", upid)

# Aggiorna config Cloud-Init
node.qemu(vmid).config.put(ipconfig0="ip=192.168.1.20/24,gw=192.168.1.1")

# Avvia
node.qemu(vmid).status.start.post()
print(f"VM Cloud-Init {vmid} avviata")
```

### pvesh equivalente
```bash
pvesh create /nodes/pve/qemu \
  --vmid 101 --name ubuntu-server-01 --ostype l26 \
  --cores 2 --memory 2048 --cpu host \
  --scsihw virtio-scsi-pci \
  --scsi0 local-lvm:32,cache=writeback,discard=on \
  --ide2 local:iso/ubuntu-22.04.3-live-server-amd64.iso,media=cdrom \
  --net0 virtio,bridge=vmbr0 --boot order=scsi0\;ide2 \
  --agent enabled=1 --onboot 1
```

---

## OPERAZIONI POST-CREAZIONE

```python
node = proxmox.nodes("pve")

# Avvia
node.qemu("101").status.start.post()
node.lxc("200").status.start.post()

# Stop / shutdown / reboot
node.qemu("101").status.stop.post()
node.qemu("101").status.shutdown.post()
node.qemu("101").status.reboot.post()

# Aggiorna config
node.qemu("101").config.put(memory=4096, cores=4)

# Ridimensiona disco
node.qemu("101").resize.put(disk="scsi0", size="+10G")

# Snapshot
upid = node.qemu("101").snapshot.post(snapname="post-install", description="Dopo installazione")
wait_task("pve", upid)

# Rollback snapshot
upid = node.qemu("101").snapshot("post-install").rollback.post()
wait_task("pve", upid)

# Elimina snapshot
node.qemu("101").snapshot("post-install").delete()

# Clone VM
upid = node.qemu("101").clone.post(newid=next_vmid(), name="vm-clone", full=1)
wait_task("pve", upid)

# Leggi config e status
config = node.qemu("101").config.get()
status = node.qemu("101").status.current.get()
print(status["status"])  # "running" / "stopped"

# Elimina VM
upid = node.qemu("101").delete()
wait_task("pve", upid)
```

---

## MONITORARE TASK (UPID)

```python
# Ottieni log di un task
upid = "UPID:pve:00002F9D:000DC5EA:57500527:vzcreate:200:root@pam:"
log = proxmox.nodes("pve").tasks(upid).log.get()
for entry in log:
    print(entry.get("t", ""))

# Lista task recenti su un nodo
tasks = proxmox.nodes("pve").tasks.get()
for t in tasks[:5]:
    print(t["upid"], t["status"])
```

---

## QUERY UTILI

```python
# Lista tutti i nodi
for node in proxmox.nodes.get():
    print(node["node"], node["status"])

# Lista tutte le VM e CT nel cluster
for vm in proxmox.cluster.resources.get(type="vm"):
    print(vm["vmid"], vm["name"], vm["type"], vm["status"])

# Lista template LXC disponibili su uno storage
contents = proxmox.nodes("pve").storage("local").content.get(content="vztmpl")
for t in contents:
    print(t["volid"])

# Lista ISO disponibili
isos = proxmox.nodes("pve").storage("local").content.get(content="iso")
for iso in isos:
    print(iso["volid"])

# Status storage
storages = proxmox.nodes("pve").storage.get()
for s in storages:
    print(s["storage"], s["type"], s.get("avail", "N/A"))
```

---

## NOTE IMPORTANTI

- `create` è sinonimo di `post`, `set` è sinonimo di `put` in proxmoxer
- Endpoint con **trattino** (es. `exec-status`) richiedono string notation: `.agent("exec-status").get()`
- Tutte le operazioni lunghe restituiscono un **UPID** — usare sempre `wait_task()` prima di procedere
- Con **UEFI/OVMF** aggiungere `efidisk0` nello stesso storage della VM
- Per **Docker dentro LXC**: `features="nesting=1,keyctl=1"` con `unprivileged=1`
- `verify_ssl=False` è necessario con certificati self-signed (default Proxmox)
- Documentazione completa: https://proxmoxer.github.io/docs/
- API viewer ufficiale: https://pve.proxmox.com/pve-docs/api-viewer/
