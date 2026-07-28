# awareness_materials.py

class AwarenessMaterials:
    def __init__(self):
        self.materials = {
            "posters": self.generate_posters(),
            "radio_spots": self.generate_radio_spots(),
            "social_posts": self.generate_social_posts(),
            "community_scripts": self.generate_community_scripts()
        }
    
    def generate_posters(self):
        """Génère des affiches de sensibilisation"""
        return {
            "prevention": {
                "title": "PROTÉGEZ-VOUS CONTRE EBOLA",
                "content": [
                    "🖐️ Lavez-vous les mains régulièrement",
                    "🚫 Évitez tout contact avec les personnes infectées",
                    "🏥 Consultez immédiatement en cas de fièvre",
                    "⚰️ Enterrements sécurisés"
                ],
                "languages": ["Français", "Lingala", "Swahili", "Kikongo", "Tshiluba"]
            },
            "symptoms": {
                "title": "RECONNAÎTRE LES SYMPTÔMES",
                "content": [
                    "🌡️ Fièvre élevée",
                    "💪 Douleurs musculaires",
                    "🤢 Vomissements",
                    "🩸 Hémorragies"
                ]
            }
        }
    
    def generate_radio_spots(self):
        """Génère des spots radio"""
        return {
            "spot_1": {
                "duration": "30s",
                "message": "Ebola: agissons ensemble. Signalez tout cas suspect au 100",
                "languages": ["Français", "Lingala", "Swahili"]
            },
            "spot_2": {
                "duration": "60s",
                "message": "Prévention Ebola: main propre, sécurité assurée. Évitez les contacts, consultez les centres de santé.",
                "languages": ["Français", "Lingala", "Swahili"]
            }
        }