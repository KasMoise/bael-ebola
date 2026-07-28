# public_communication.py

class PublicCommunication:
    def __init__(self):
        self.channels = {
            "radio": self.broadcast_radio,
            "tv": self.broadcast_tv,
            "social_media": self.post_social_media,
            "community": self.community_outreach
        }
        
        self.templates = {
            "alert": "🚨 ALERTE EBOLA à {zone}: {cases} nouveaux cas. Mesures: {measures}",
            "prevention": "🛡️ Prévention Ebola: Lavez-vous les mains, évitez tout contact, consultez immédiatement si fièvre.",
            "update": "📊 Évolution Ebola: {status}. Restez vigilants.",
            "info": "ℹ️ Centre de traitement le plus proche: {location}. Contact: {phone}"
        }
    
    def send_public_alert(self, alert_data):
        """Envoie des alertes au public"""
        message = self.templates["alert"].format(
            zone=alert_data["zone"],
            cases=alert_data["cases"],
            measures=alert_data["measures"]
        )
        
        for channel in self.get_active_channels():
            self.channels[channel](message)
    
    def community_outreach(self, message):
        """Sensibilisation communautaire"""
        community_leaders = self.get_community_leaders()
        
        for leader in community_leaders:
            self.send_sms(leader.phone, message)
            self.schedule_meeting(leader, message)