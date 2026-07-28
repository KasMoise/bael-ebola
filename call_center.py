# call_center.py

class CallCenter:
    def __init__(self):
        self.agents = self.load_agents()
        self.faq = self.load_faq()
        self.emergency_protocol = self.load_protocol()
    
    def handle_call(self, caller_info, query):
        """Gère les appels entrants"""
        intent = self.classify_intent(query)
        
        if intent == "emergency":
            return self.emergency_response(caller_info)
        elif intent == "symptom_check":
            return self.symptom_check(query)
        elif intent == "report_case":
            return self.report_case(caller_info, query)
        elif intent == "general":
            return self.general_response(query)
        else:
            return self.transfer_to_agent(caller_info)
    
    def symptom_check(self, query):
        """Vérification des symptômes"""
        symptoms = self.extract_symptoms(query)
        risk_score = self.assess_symptoms(symptoms)
        
        if risk_score > 0.7:
            return {
                "message": "Vos symptômes nécessitent une consultation immédiate.",
                "action": "Consultez le centre de santé le plus proche.",
                "location": self.find_nearest_health_center()
            }
        else:
            return {
                "message": "Suivez les mesures préventives et surveillez votre état.",
                "action": "Consultez si les symptômes persistent.",
                "advice": self.get_prevention_advice()
            }