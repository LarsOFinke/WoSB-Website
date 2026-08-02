const en = {
  footerLink: 'Privacy', eyebrow: 'Privacy center', title: 'Privacy and data rights', description: 'Understand what is stored, manage your choices and contact the privacy administrators.',
  processingTitle: 'Data processing', processingText: 'We process account, profile and community content only to provide the fleet platform. General visitor or request tracking is disabled.',
  cookiesTitle: 'Cookies and local storage', cookiesText: 'Login and the saved privacy choice use first-party cookies. Language and interface preferences remain on this device. No analytics service or advertising tracker is currently connected.',
  retentionTitle: 'Retention and deletion', retentionText: 'Operational records have fixed deletion periods. A verified deletion request removes profile and membership data, revokes sessions and pseudonymizes the account; content requiring a community or legal review is handled individually.',
  recipientsTitle: 'Recipients', recipientsText: 'Configured Discord and Raid-Helper integrations receive only explicitly selected operational events. Privacy messages and resolution notes are not sent to Discord.',
  contactTitle: 'Contact about privacy', contactText: 'Send a confidential question to the administrators. Only a reply address, subject and message are stored. Resolved messages follow the privacy-request retention period.',
  email: 'Reply email', subject: 'Subject', message: 'Message', submit: 'Send privacy message', contactSuccess: 'Your message was submitted to the privacy administrators.', contactError: 'The privacy message could not be submitted.',
  adminContactsTitle: 'Privacy contact inbox', adminContactsEmpty: 'No privacy contact messages.',
}

const de = {
  footerLink: 'Datenschutz', eyebrow: 'Datenschutz-Center', title: 'Datenschutz und Betroffenenrechte', description: 'Nachvollziehen, welche Daten gespeichert werden, Einstellungen verwalten und die Datenschutz-Administratoren kontaktieren.',
  processingTitle: 'Datenverarbeitung', processingText: 'Account-, Profil- und Community-Inhalte werden nur für den Betrieb der Flottenplattform verarbeitet. Allgemeines Besucher- oder Request-Tracking ist deaktiviert.',
  cookiesTitle: 'Cookies und lokaler Speicher', cookiesText: 'Anmeldung und Datenschutzauswahl verwenden First-Party-Cookies. Sprache und Oberflächeneinstellungen verbleiben auf diesem Gerät. Es ist derzeit kein Analyse- oder Werbetracker angebunden.',
  retentionTitle: 'Aufbewahrung und Löschung', retentionText: 'Betriebsdaten besitzen feste Löschfristen. Ein bestätigter Löschantrag entfernt Profil- und Mitgliedschaftsdaten, widerruft Sessions und pseudonymisiert den Account; Inhalte mit Community- oder rechtlicher Relevanz werden einzeln geprüft.',
  recipientsTitle: 'Empfänger', recipientsText: 'Konfigurierte Discord- und Raid-Helper-Integrationen erhalten nur ausdrücklich ausgewählte Betriebsereignisse. Datenschutz-Nachrichten und Bearbeitungsvermerke werden nicht an Discord gesendet.',
  contactTitle: 'Kontakt zum Datenschutz', contactText: 'Sende eine vertrauliche Frage an die Administratoren. Gespeichert werden nur Antwortadresse, Betreff und Nachricht. Abgeschlossene Nachrichten folgen der Aufbewahrungsfrist für Datenschutzanträge.',
  email: 'Antwort-E-Mail', subject: 'Betreff', message: 'Nachricht', submit: 'Datenschutz-Nachricht senden', contactSuccess: 'Deine Nachricht wurde an die Datenschutz-Administratoren übermittelt.', contactError: 'Die Datenschutz-Nachricht konnte nicht übermittelt werden.',
  adminContactsTitle: 'Datenschutz-Kontaktpostfach', adminContactsEmpty: 'Keine Datenschutz-Nachrichten vorhanden.',
}

export const privacyCenterMessages = {
  en: { privacy: { center: en } }, de: { privacy: { center: de } },
  fr: { privacy: { center: { ...en, footerLink: 'Confidentialité', eyebrow: 'Centre de confidentialité', recipientsTitle: 'Destinataires', contactTitle: 'Contact confidentialité', subject: 'Objet', message: 'Votre message', submit: 'Envoyer le message', contactError: 'Le message n’a pas pu être envoyé.' } } },
  es: { privacy: { center: { ...en, footerLink: 'Privacidad', eyebrow: 'Centro de privacidad', recipientsTitle: 'Destinatarios', contactTitle: 'Contacto de privacidad', subject: 'Asunto', message: 'Mensaje', submit: 'Enviar mensaje', contactError: 'No se pudo enviar el mensaje.' } } },
  pt: { privacy: { center: { ...en, footerLink: 'Privacidade', eyebrow: 'Centro de privacidade', recipientsTitle: 'Destinatários', contactTitle: 'Contacto de privacidade', subject: 'Assunto', message: 'Mensagem', submit: 'Enviar mensagem', contactError: 'Não foi possível enviar a mensagem.' } } },
  ru: { privacy: { center: { ...en, footerLink: 'Конфиденциальность', eyebrow: 'Центр конфиденциальности', recipientsTitle: 'Получатели', contactTitle: 'Связь по вопросам конфиденциальности', subject: 'Тема', message: 'Сообщение', submit: 'Отправить сообщение', contactError: 'Не удалось отправить сообщение.' } } },
  cn: { privacy: { center: { ...en, footerLink: '隐私', eyebrow: '隐私中心', recipientsTitle: '接收方', contactTitle: '隐私联系', subject: '主题', message: '消息', submit: '发送隐私消息', contactError: '无法发送隐私消息。' } } },
}
