# 🚀 Git & GitHub Workflow Guide

Questa guida descrive il processo standard per aggiungere funzionalità o correggere errori (bug fix) in questo progetto in modo sicuro e pulito.

---

## 🏗️ 1. Preparazione: Pulizia del Branch Main
Prima di iniziare qualsiasi nuovo lavoro, assicurati che la tua copia locale sia aggiornata con l'ultima versione di GitHub.

```bash
# Sostituisci il tuo ramo locale sul "Main"
git checkout main

# Scarica le ultime modifiche ufficiali da GitHub
git pull origin main
```

## 🌿 2. Creazione di un nuovo Branch (Ramo)
**Mai lavorare direttamente su `main`!** Crea sempre un "ramo" separato per i tuoi esperimenti. Usa un nome descrittivo.

```bash
# Esempio: git checkout -b fix/disk-resize
git checkout -b <nome-del-branch>
```

## 💻 3. Sviluppo e Salvataggio (Commit)
Fai le tue modifiche al codice. Quando sei soddisfatto di un pezzetto di lavoro, salvalo localmente:

```bash
# Vedi cosa hai cambiato
git status

# Aggiungi i file cambiati ("stage")
git add . 

# Crea un salvataggio con un messaggio descrittivo
git commit -m "feat(provisioner): aggiunto ridimensionamento disco"
```

## ⬆️ 4. Sincronizzazione con GitHub (Push)
Invia il tuo branch locale su GitHub per poter creare una Pull Request.

```bash
# La prima volta che invii un nuovo branch
git push -u origin <nome-del-branch>
```

## 🟢 5. Pull Request (PR) su GitHub
Vai sulla pagina del repository su GitHub nel browser:

1. Vedrai un pulsante verde **"Compare & pull request"**: cliccalo.
2. Scrivi una breve descrizione di cosa hai cambiato.
3. Clicca su **"Create pull request"**.
4. Se il test (o il tuo controllo) è ok, clicca su **"Merge pull request"**. 

*A questo punto, il tuo codice è ufficialmente parte del ramo `main` su GitHub!*

## 🧹 6. Pulizia Finale e Chiusura del Ciclo
Torna nel terminale per preparare il terreno per il prossimo lavoro:

```bash
# Torna sul main locale
git checkout main

# Scarica le modifiche appena unite da GitHub (molto importante!)
git pull origin main

# (Opzionale) Cancella il branch locale vecchio che non serve più
git branch -d <nome-del-branch>
```

---

> [!TIP]
> **In caso di errori:** Se qualcosa va storto sul tuo branch e non sai come uscirne, puoi sempre cancellarlo e ricominciare da capo partendo da `main`. Non rischierai mai di rovinare la versione "ufficiale" del codice!
