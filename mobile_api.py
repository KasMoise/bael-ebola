# mobile_api.py - API pour l'application mobile

from fastapi import FastAPI, File, UploadFile
import pandas as pd

app = FastAPI(title="BAEL-Ebola Mobile API")

@app.post("/report")
async def report_case(
    zone: str,
    patient_name: str,
    age: int,
    gender: str,
    symptoms: List[str],
    date: datetime,
    contact_tracing: bool = False
):
    """
    Signalement de cas en temps réel par les agents de santé
    """
    # Enregistrer le cas dans la base de données
    case_id = save_case(zone, patient_name, age, gender, symptoms, date)
    
    # Vérifier les contacts à risque
    if contact_tracing:
        contacts = trace_contacts(zone, patient_name)
        notify_contacts(contacts)
    
    # Mettre à jour les prédictions
    update_predictions(zone)
    
    return {
        "status": "success",
        "case_id": case_id,
        "risk_assessment": assess_risk(symptoms),
        "recommended_action": get_recommendation(symptoms)
    }

@app.post("/upload-batch")
async def upload_batch(file: UploadFile):
    """
    Importation massive de données depuis les zones reculées
    """
    df = pd.read_csv(file.file)
    cases = process_batch(df)
    return {"processed": len(cases), "status": "success"}