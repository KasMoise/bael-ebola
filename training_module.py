# training_module.py

class TrainingModule:
    def __init__(self):
        self.courses = {
            "basic": "Introduction à Ebola et au système BAEL",
            "intermediate": "Utilisation du Dashboard et des Outils d'Alerte",
            "advanced": "Analyse de Données et Prise de Décision"
        }
    
    def get_training_content(self, level, user_role):
        """Contenu de formation adapté"""
        return {
            "modules": self.get_modules(level),
            "videos": self.get_videos(level),
            "exercises": self.get_exercises(level),
            "certification": self.get_certification(level)
        }
    
    def track_progress(self, user_id):
        """Suivi de la progression de formation"""
        progress = self.get_user_progress(user_id)
        return {
            "completed_modules": progress["completed"],
            "score": progress["score"],
            "certification_status": progress["certification"],
            "recommendations": self.get_recommendations(progress)
        }