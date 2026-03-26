PRD: Proxmox Self Service Portal
1. Product overview
1.1 Document title and version
PRD: Proxmox Self Service Portal

Version: 1.1.0

1.2 Product summary
Questo progetto consiste in un'applicazione web self-service che permette agli utenti di richiedere e gestire in autonomia macchine virtuali (VM) e container (LXC) su un'infrastruttura Proxmox VE. L'obiettivo è decentralizzare la creazione di risorse IT, fornendo interfacce semplici per utenti non esperti.

Il sistema memorizza le richieste come "job" in un database locale. Un processo di automazione (Cronjob) elabora queste code periodicamente, clonando i template predefiniti, configurando l'hardware e assegnando il bridge di rete scelto dall'utente in fase di ordine. Questo garantisce un controllo granulare sulle risorse e una maggiore stabilità del cluster Proxmox.

2. Goals
2.1 Business goals
Ridurre il carico di lavoro manuale degli amministratori di sistema per il provisioning di risorse standard.

Ottimizzare l'utilizzo delle risorse del server tramite taglie predefinite.

Monitorare e tracciare l'utilizzo delle risorse tramite un database centralizzato.

2.2 User goals
Ottenere rapidamente un ambiente di test o sviluppo configurato correttamente a livello di rete.

Gestire il ciclo di vita delle proprie risorse in totale autonomia.

Interfaccia semplificata per evitare errori di configurazione complessi.

2.3 Non-goals
Sostituire interamente l'interfaccia di amministrazione di Proxmox (PVE GUI).

Gestire configurazioni hardware personalizzate oltre le taglie definite.

Gestire backup o snapshot avanzati tramite questo portale.

3. User personas
3.1 Key user types
Utente Standard (Sviluppatore/Tester)

Amministratore di Sistema (Superuser)

3.2 Basic persona details
Developer Dave: Uno sviluppatore che ha bisogno di una VM pulita su una specifica VLAN (bridge) per testare un'applicazione isolata.

Admin Alice: Monitora il database dei job e si assicura che il cronjob stia processando correttamente le richieste di rete e risorse.

3.3 Role-based access
User: Può registrarsi, loggarsi, richiedere risorse (specificando tipo, taglia e bridge), vedere le proprie macchine e cancellarle.

Admin: Può visualizzare e gestire tutte le richieste nel database per tutti gli utenti.

4. Functional requirements
Autenticazione utente (Priority: High)

Registrazione account e login sicuro (Flask-Login / FastAPI Auth).

Richiesta risorsa con configurazione di rete (Priority: High)

Scelta tra VM o Container.

Selezione della taglia (Tiny, Medium, High).

Selezione del Network Bridge: L'utente sceglie obbligatoriamente il bridge (es. vmbr0 per rete standard o vmbr0.50 per VLAN 50) durante la richiesta.

Gestione taglie predefinite (Priority: High)

Tiny: 1 vCPU, 1GB RAM, 10GB Disk.

Medium: 2 vCPU, 4GB RAM, 40GB Disk.

High: 4 vCPU, 8GB RAM, 80GB Disk.

Automazione Provisioning (Cronjob) (Priority: High)

Script Python che processa i job: clona il template e imposta l'interfaccia di rete sul bridge selezionato dall'utente.

Dashboard utente (Priority: High)

Lista delle macchine con stato (Pending, Active, Deleted).

Opzione per eliminare la risorsa.

5. User experience
5.1 Entry points & first-time user flow
Pagina di login/registrazione Bootstrap.

Dashboard principale "I miei Lab" con pulsante "Nuova Richiesta".

5.2 Core experience
Form di richiesta: L'utente seleziona Tipo (VM/CT), Taglia e il Bridge di rete da un menu a tendina. Cliccando su "Invia", la richiesta entra nel database in stato "Pending".

Feedback visivo: Un avviso informa l'utente che la macchina sarà pronta al prossimo ciclo di automazione.

5.3 Advanced features & edge cases
Se il bridge selezionato non è disponibile sul nodo Proxmox scelto per la clonazione, il job deve restituire un errore "Failed".

Conferma di eliminazione obbligatoria per prevenire cancellazioni involontarie.

5.4 UI/UX highlights
Utilizzo di componenti Bootstrap 5 per una UI responsive.

Badge colorati per distinguere a colpo d'occhio la rete (es. Blue per Standard, Orange per VLAN).

6. Narrative
L'utente accede al portale e richiede un container di taglia "Tiny" specificando il bridge vmbr0.50 perché deve lavorare in una sottorete protetta. Il sistema valida i dati e salva il job. Al minuto stabilito, il cronjob rileva la richiesta, comanda a Proxmox tramite proxmoxer di clonare il template LXC e, subito dopo la clonazione, ne configura l'interfaccia di rete sul bridge richiesto. L'utente riceve la sua risorsa già pronta e collegata alla rete corretta senza ulteriori interventi.

7. Success metrics
7.1 User-centric metrics
Tasso di completamento del form di richiesta al primo tentativo.

Tempo di attesa tra richiesta e disponibilità effettiva.

7.2 Business metrics
Riduzione del tempo speso dagli admin per configurazioni di rete manuali.

7.3 Technical metrics
Success rate del cronjob di provisioning (> 98%).

Correttezza dell'assegnazione bridge verificata post-clonazione.

8. Technical considerations
8.1 Integration points
Proxmoxer: Libreria Python per interazione API.

FastAPI/Flask: Web framework per la gestione delle richieste e del DB.

8.2 Data storage & privacy
Database (SQLite/PostgreSQL) per memorizzare i parametri della macchina inclusa la specifica del bridge di rete.

8.3 Scalability & performance
Il provisioning asincrono evita il blocco dell'interfaccia web durante le operazioni pesanti di Proxmox.

8.4 Potential challenges
Gestione dei permessi: assicurarsi che l'utente Proxmox usato dall'app abbia i permessi per modificare le interfacce di rete (Network.Config).

9. Milestones & sequencing
9.1 Project estimate
Medium: 3-4 settimane.

9.2 Team size & composition
1 Developer (Full-stack Python).

9.3 Suggested phases
Fase 1: Auth e Database Schema (incluso campo Bridge).

Fase 2: Implementazione logica Proxmoxer per clone + network config.

Fase 3: Sviluppo Frontend con form integrato.

Fase 4: Testing end-to-end e gestione Cron.

10. User stories
10.1 Authentication
ID: GH-001

Description: Come utente, voglio registrarmi e loggarmi per gestire le mie risorse.

Acceptance criteria: Login funzionante con gestione sessione.

10.2 Resource Request with Bridge
ID: GH-002

Description: Come utente, voglio selezionare Tipo, Taglia e Bridge (es. vmbr0) in un unico modulo di richiesta.

Acceptance criteria: Il DB salva correttamente l'associazione bridge-macchina.

10.3 Dashboard Listing
ID: GH-003

Description: Come utente, voglio vedere lo stato della mia richiesta e su quale bridge è stata configurata.

Acceptance criteria: Visualizzazione chiara dei dettagli tecnici nella dashboard.

10.4 Cronjob Automation
ID: GH-004

Description: Come sistema, voglio clonare il template e impostare il bridge di rete corretto automaticamente.

Acceptance criteria: La macchina su Proxmox deve avere l'interfaccia net0 collegata al bridge scelto dall'utente.

10.5 Resource Deletion
ID: GH-005

Description: Come utente, voglio eliminare la risorsa quando non più necessaria.

Acceptance criteria: Rimozione completa da Proxmox e aggiornamento DB.