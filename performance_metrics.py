# performance_metrics.py

class PerformanceMetrics:
    def __init__(self):
        self.metrics = {
            "detection": {
                "time_to_detection": 0, # Heures
                "cases_detected": 0,
                "false_positives": 0
            },
            "response": {
                "response_time": 0, # Heures
                "containment_rate": 0, # Pourcentage
                "recovery_rate": 0
            },
            "system": {
                "uptime": 0, # Pourcentage
                "accuracy": 0, # Pourcentage
                "user_satisfaction": 0 # Sur 10
            }
        }
    
    def update_detection_metrics(self, cases):
        self.metrics["detection"]["cases_detected"] += len(cases)
        self.metrics["detection"]["time_to_detection"] = self.calculate_detection_time()
    
    def generate_report(self):
        """Génère un rapport de performance"""
        return {
            "period": self.get_period(),
            "metrics": self.metrics,
            "trends": self.analyze_trends(),
            "recommendations": self.generate_recommendations()
        }