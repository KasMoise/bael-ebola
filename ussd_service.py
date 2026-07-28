# ussd_service.py - Service USSD pour téléphones mobiles

class USSDService:
    def __init__(self):
        self.menu_options = {
            "1": "Signaler un cas suspect",
            "2": "Consulter les alertes",
            "3": "Recommandations de prévention",
            "4": "Contacter le centre d'urgence"
        }
    
    def process_ussd(self, session_id, phone_number, input_text):
        """Traitement des requêtes USSD"""
        if input_text == "":
            return self.main_menu()
        
        if input_text == "1":
            return self.report_case_menu(phone_number)
        
        if input_text == "2":
            return self.get_alerts()
        
        if input_text == "3":
            return self.get_prevention_tips()
        
        if input_text == "4":
            return self.get_emergency_contacts()
    
    def report_case_menu(self, phone_number):
        return "CON Entrez les informations du cas:\n" + \
               "1. Âge\n" + \
               "2. Symptômes\n" + \
               "3. Contact avec un cas confirmé"
    
    def get_alerts(self):
        alerts = fetch_alerts()
        return f"END Alerte Ebola {alerts['zone']}: {alerts['message']}"