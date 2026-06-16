🏠 AI Risk Assessment for Insurance using CPTED


![AI Challenge](https://img.shields.io/badge/AI%20Challenge-3rd%20Place-brightgreen)

![Python](https://img.shields.io/badge/Python-3.x-blue)

![YOLOv8](https://img.shields.io/badge/YOLOv8-Instance%20Segmentation-orange)



🏆 AI Challenge Project – Master AI \& Data Analytics for Business



Questo progetto è stato sviluppato nell’ambito della \*\*AI Challenge\*\* del Master \*\*AI \& Data Analytics for Business\*\*, con l’obiettivo di applicare tecniche di Intelligenza Artificiale e Data Analytics a un caso d’uso reale nel settore assicurativo.



Il progetto ha ottenuto il \*\*3° posto nella competizione\*\*, grazie alla proposta di un sistema innovativo per la valutazione automatizzata del rischio assicurativo immobiliare attraverso l’integrazione di dati strutturati, analisi territoriale e computer vision.





📌 Descrizione del Progetto



Questo progetto propone un sistema di intelligenza artificiale per la valutazione del rischio assicurativo immobiliare basato sulla teoria \*\*CPTED (Crime Prevention Through Environmental Design)\*\*.



L’obiettivo è supportare il processo di valutazione assicurativa attraverso uno strumento decisionale avanzato capace di integrare dati strutturati dell’abitazione, informazioni territoriali e analisi di immagini satellitari per generare uno \*\*score di rischio dell’immobile e della zona circostante\*\*.



Il modello combina diverse fonti di dati:



\- 🏠 \*\*Dati dell’immobile:\*\* metri quadri, presenza di sistemi di allarme, caratteristiche strutturali e informazioni relative all’abitazione.

\- 🛣️ \*\*Feature territoriali e stradali:\*\* estratte tramite \*\*OpenStreetMap\*\*.

\- 🛰️ \*\*Feature ambientali:\*\* ottenute tramite immagini satellitari di Google Maps recuperate a partire dall’indirizzo dell’immobile.

\- 👁️ \*\*Analisi visiva:\*\* tramite \*\*YOLOv8 Instance Segmentation\*\* per identificare elementi rilevanti presenti nelle immagini satellitari.



Le feature estratte vengono integrate in un modello \*\*AdaBoost\*\*, che genera uno scoring del rischio consultabile attraverso un’interfaccia grafica dedicata agli assicuratori.





⚙️ Tecnologie Utilizzate



\- Python

\- AdaBoost (Machine Learning)

\- YOLOv8 (Instance Segmentation)

\- OpenStreetMap API

\- Google Maps Satellite API

\- Roboflow (Dataset labeling)

\- Streamlit (Interfaccia grafica)







📂 Struttura del Repository



├── coding/

│ ├── APP/

│ │ └── Codice per applicazione Streamlit

│ │

│ ├── Script Python per:

│ │ ├── preprocessing dati

│ │ ├── feature extraction

│ │ ├── analisi immagini satellitari

│ │ └── training modello

│ │

│ └── Modello YOLOv8

│

├── dataset/

│ ├── CSV delle abitazioni e dei sinistri forniti

│ └── Dataset annotato con Roboflow per YOLOv8

│

├── output/

│ └── File CSV generati dagli script

│

├── output\_satellite\_maps/

│ └── Immagini satellitari Google Maps

│

├── output\_satellite\_maps\_zoom/

│ └── Immagini satellitari con zoom maggiore

│

├── Paper\_CPTED.pdf

│

└── Presentazione.pdf





🔎 Pipeline del Sistema



1\. Raccolta dei dati dell’immobile.

2\. Estrazione delle feature territoriali tramite OpenStreetMap.

3\. Recupero delle immagini satellitari tramite indirizzo dell’abitazione.

4\. Analisi delle immagini tramite YOLOv8 Instance Segmentation.

5\. Fusione delle feature estratte.

6\. Addestramento e valutazione del modello AdaBoost.

7\. Generazione dello score di rischio.

8\. Visualizzazione tramite interfaccia grafica.





🚀 Possibili Applicazioni



\- Supporto alla valutazione del rischio assicurativo.

\- Automazione delle perizie immobiliari.

\- Analisi preventiva della sicurezza urbana.

\- Supporto alle decisioni di underwriting assicurativo.





&#x20;📚 Riferimenti



\- \*\*CPTED – Crime Prevention Through Environmental Design\*\*  

&#x20; Vedi: `Paper\_CPTED.pdf`



\- \*\*Presentazione completa del progetto\*\*  

&#x20; Vedi: `Presentazione.pdf`





⚠️ Note sul Repository



Questo repository rappresenta il risultato di un progetto sviluppato durante una \*\*AI Challenge del Master AI \& Data Analytics for Business\*\*.



Alcune componenti sono state ottimizzate per la dimostrazione del concept e potrebbero richiedere ulteriori integrazioni per un utilizzo in ambiente produttivo.



Per via dei limiti di dimensione imposti da GitHub, non è stato possibile caricare l’intero set di dati utilizzato durante lo sviluppo del progetto. Alcuni file, in particolare quelli relativi alle immagini satellitari e ai dataset completi, sono stati quindi esclusi dal repository.



Il progetto ha principalmente finalità dimostrative e accademiche. L’obiettivo è mostrare l’approccio metodologico, le tecniche impiegate e il funzionamento generale della pipeline.



