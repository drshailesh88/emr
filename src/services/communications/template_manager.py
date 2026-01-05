"""Template manager for bilingual message templates."""

import logging
from dataclasses import dataclass
from typing import Dict, Optional
import re

logger = logging.getLogger(__name__)


@dataclass
class MessageTemplate:
    """Message template with bilingual support."""
    name: str
    content_en: str
    content_hi: str
    variables: list


class TemplateManager:
    """Manages message templates with bilingual support (English + Hindi)."""

    # Predefined templates
    TEMPLATES = {
        "appointment_reminder": {
            "en": "Dear {patient_name}, this is a reminder for your appointment with {doctor_name} at {clinic_name} on {date} at {time}. Please arrive 15 minutes early. Reply CANCEL to reschedule.",
            "hi": "प्रिय {patient_name}, यह आपकी {date} को {time} बजे {clinic_name} में {doctor_name} के साथ अपॉइंटमेंट का रिमाइंडर है। कृपया 15 मिनट पहले पहुंचें। रद्द करने के लिए CANCEL भेजें।",
            "vars": ["patient_name", "doctor_name", "clinic_name", "date", "time"]
        },
        "follow_up_reminder": {
            "en": "Dear {patient_name}, your follow-up visit with {doctor_name} is due on {date}. Please call {clinic_phone} to book an appointment. Your health matters!",
            "hi": "प्रिय {patient_name}, आपकी {date} को {doctor_name} के साथ फॉलो-अप विज़िट है। कृपया {clinic_phone} पर कॉल करके अपॉइंटमेंट बुक करें। आपका स्वास्थ्य महत्वपूर्ण है!",
            "vars": ["patient_name", "doctor_name", "date", "clinic_phone"]
        },
        "medication_reminder": {
            "en": "Dear {patient_name}, reminder to take your {medication} ({dose}) - {frequency}. {instructions}. Stay healthy!",
            "hi": "प्रिय {patient_name}, अपनी {medication} ({dose}) - {frequency} लेने का रिमाइंडर। {instructions}। स्वस्थ रहें!",
            "vars": ["patient_name", "medication", "dose", "frequency", "instructions"]
        },
        "lab_due": {
            "en": "Dear {patient_name}, your {test_name} test is due on {due_date}. Please visit {clinic_name} or call {clinic_phone} to schedule. Early detection saves lives!",
            "hi": "प्रिय {patient_name}, आपका {test_name} परीक्षण {due_date} को है। कृपया {clinic_name} पर जाएं या {clinic_phone} पर कॉल करके शेड्यूल करें। प्रारंभिक जांच जीवन बचाती है!",
            "vars": ["patient_name", "test_name", "due_date", "clinic_name", "clinic_phone"]
        },
        "health_tip": {
            "en": "Health Tip from {clinic_name}: {tip}. Stay healthy, stay happy! For appointments: {clinic_phone}",
            "hi": "{clinic_name} से स्वास्थ्य सुझाव: {tip}। स्वस्थ रहें, खुश रहें! अपॉइंटमेंट के लिए: {clinic_phone}",
            "vars": ["clinic_name", "tip", "clinic_phone"]
        },
        "clinic_notice": {
            "en": "Notice from {clinic_name}: {notice}. For queries, call {clinic_phone}. Thank you for your understanding.",
            "hi": "{clinic_name} से सूचना: {notice}। पूछताछ के लिए {clinic_phone} पर कॉल करें। आपकी समझ के लिए धन्यवाद।",
            "vars": ["clinic_name", "notice", "clinic_phone"]
        },
        "preventive_care_annual": {
            "en": "Dear {patient_name}, it's time for your annual health checkup! Please call {clinic_phone} to schedule. Prevention is better than cure.",
            "hi": "प्रिय {patient_name}, आपके वार्षिक स्वास्थ्य चेकअप का समय है! कृपया {clinic_phone} पर कॉल करके शेड्यूल करें। रोकथाम इलाज से बेहतर है।",
            "vars": ["patient_name", "clinic_phone"]
        },
        "prescription_ready": {
            "en": "Dear {patient_name}, your prescription is ready for pickup at {clinic_name}. Valid until {expiry_date}. Office hours: {office_hours}",
            "hi": "प्रिय {patient_name}, आपका प्रिस्क्रिप्शन {clinic_name} पर पिकअप के लिए तैयार है। {expiry_date} तक वैध। ऑफिस समय: {office_hours}",
            "vars": ["patient_name", "clinic_name", "expiry_date", "office_hours"]
        },
        "birthday_wishes": {
            "en": "Happy Birthday {patient_name}! 🎉 Wishing you a healthy and joyful year ahead. - Team {clinic_name}",
            "hi": "जन्मदिन मुबारक {patient_name}! 🎉 आपको स्वस्थ और खुशहाल वर्ष की शुभकामनाएं। - टीम {clinic_name}",
            "vars": ["patient_name", "clinic_name"]
        },
        "test_results_ready": {
            "en": "Dear {patient_name}, your {test_name} results are ready. Please visit the clinic or call {clinic_phone} to discuss with {doctor_name}.",
            "hi": "प्रिय {patient_name}, आपके {test_name} परिणाम तैयार हैं। कृपया क्लिनिक पर जाएं या {doctor_name} से चर्चा करने के लिए {clinic_phone} पर कॉल करें।",
            "vars": ["patient_name", "test_name", "clinic_phone", "doctor_name"]
        }
    }

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize template manager.

        Args:
            db_path: Optional path to SQLite database for custom templates
        """
        self.db_path = db_path
        self.custom_templates: Dict[str, dict] = {}

    def get_template(self, template_type: str, language: str = "en") -> Optional[str]:
        """
        Get message template by type and language.

        Args:
            template_type: Type of template (appointment_reminder, follow_up_reminder, etc.)
            language: Language code ('en' or 'hi')

        Returns:
            Template string with placeholders, or None if not found

        Example:
            >>> tm = TemplateManager()
            >>> template = tm.get_template("appointment_reminder", "en")
            >>> print(template)
            "Dear {patient_name}, this is a reminder..."
        """
        # Check custom templates first
        if template_type in self.custom_templates:
            template_data = self.custom_templates[template_type]
            lang_key = f"content_{language}"
            if lang_key in template_data:
                return template_data[lang_key]

        # Fall back to predefined templates
        if template_type in self.TEMPLATES:
            return self.TEMPLATES[template_type].get(language)

        logger.warning(f"Template '{template_type}' not found for language '{language}'")
        return None

    def render_template(self, template: str, variables: Dict[str, str]) -> str:
        """
        Render template by replacing placeholders with actual values.

        Args:
            template: Template string with {placeholder} variables
            variables: Dictionary of variable names to values

        Returns:
            Rendered message with all placeholders replaced

        Example:
            >>> tm = TemplateManager()
            >>> template = "Dear {patient_name}, appointment on {date}"
            >>> rendered = tm.render_template(template, {
            ...     "patient_name": "Ram Lal",
            ...     "date": "2024-01-15"
            ... })
            >>> print(rendered)
            "Dear Ram Lal, appointment on 2024-01-15"
        """
        try:
            return template.format(**variables)
        except KeyError as e:
            missing_var = str(e).strip("'")
            logger.error(f"Missing variable '{missing_var}' in template rendering")
            # Replace missing variables with placeholder
            return re.sub(r'\{' + missing_var + r'\}', f'[{missing_var}]', template)
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return template

    def create_custom_template(
        self,
        name: str,
        content_en: str,
        content_hi: str,
        variables: Optional[list] = None
    ) -> bool:
        """
        Create a custom template.

        Args:
            name: Unique template name
            content_en: English template content
            content_hi: Hindi template content
            variables: List of variable names used in template

        Returns:
            True if created successfully, False otherwise

        Example:
            >>> tm = TemplateManager()
            >>> tm.create_custom_template(
            ...     "welcome_new_patient",
            ...     "Welcome {patient_name} to {clinic_name}!",
            ...     "स्वागत है {patient_name} {clinic_name} में!",
            ...     ["patient_name", "clinic_name"]
            ... )
            True
        """
        try:
            if variables is None:
                # Extract variables from template
                variables = list(set(
                    re.findall(r'\{(\w+)\}', content_en) +
                    re.findall(r'\{(\w+)\}', content_hi)
                ))

            self.custom_templates[name] = {
                "content_en": content_en,
                "content_hi": content_hi,
                "vars": variables
            }

            logger.info(f"Custom template '{name}' created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating custom template '{name}': {e}")
            return False

    def delete_custom_template(self, name: str) -> bool:
        """
        Delete a custom template.

        Args:
            name: Template name to delete

        Returns:
            True if deleted, False if not found or error
        """
        if name in self.custom_templates:
            del self.custom_templates[name]
            logger.info(f"Custom template '{name}' deleted")
            return True
        logger.warning(f"Custom template '{name}' not found")
        return False

    def get_template_variables(self, template_type: str) -> Optional[list]:
        """
        Get list of variables used in a template.

        Args:
            template_type: Type of template

        Returns:
            List of variable names, or None if template not found
        """
        if template_type in self.custom_templates:
            return self.custom_templates[template_type].get("vars", [])

        if template_type in self.TEMPLATES:
            return self.TEMPLATES[template_type].get("vars", [])

        return None

    def list_templates(self) -> Dict[str, list]:
        """
        List all available templates.

        Returns:
            Dictionary with 'predefined' and 'custom' template lists
        """
        return {
            "predefined": list(self.TEMPLATES.keys()),
            "custom": list(self.custom_templates.keys())
        }

    def render(
        self,
        template_type: str,
        variables: Dict[str, str],
        language: str = "en"
    ) -> Optional[str]:
        """
        Convenience method to get and render template in one call.

        Args:
            template_type: Type of template
            variables: Dictionary of variables
            language: Language code ('en' or 'hi')

        Returns:
            Rendered message, or None if template not found

        Example:
            >>> tm = TemplateManager()
            >>> message = tm.render("appointment_reminder", {
            ...     "patient_name": "Ram Lal",
            ...     "doctor_name": "Dr. Sharma",
            ...     "clinic_name": "DocAssist Clinic",
            ...     "date": "15-Jan-2024",
            ...     "time": "10:00 AM"
            ... })
        """
        template = self.get_template(template_type, language)
        if template is None:
            return None
        return self.render_template(template, variables)
