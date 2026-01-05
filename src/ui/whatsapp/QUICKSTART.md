# WhatsApp Integration Quick Start

Get WhatsApp messaging working in DocAssist EMR in 5 minutes!

## Option 1: Mock Mode (No Credentials - Recommended for Testing)

Perfect for demos, development, and testing without WhatsApp Business API credentials.

### Step 1: Run Setup
```bash
cd /home/user/emr
python setup_whatsapp.py
```

### Step 2: Enable Mock Mode
1. Launch DocAssist EMR
2. Go to **Settings**
3. Click **WhatsApp** tab (you'll need to add this - see INTEGRATION_GUIDE.md)
4. Check **"Enable WhatsApp Features"**
5. Check **"Mock Mode (Log messages instead of sending)"**
6. Click **Save Settings**

### Step 3: Test It
1. Open a patient record
2. Create a prescription
3. Click **"Share WhatsApp"** button
4. Fill in phone number
5. Click **"Send Message"**
6. Check your console/terminal - you'll see the message logged!

**Example Console Output:**
```
[MOCK MODE] Would send WhatsApp message to +919876543210:
Dear Rajesh Kumar,
Your prescription from your visit on 15 January 2024 is ready...
```

**That's it!** All WhatsApp features work in mock mode without any external setup.

---

## Option 2: Production Mode (With WhatsApp Business Credentials)

For actually sending messages via WhatsApp.

### Step 1: Get WhatsApp Business API Credentials

1. Go to [Meta Business Suite](https://business.facebook.com)
2. Click **WhatsApp** in the left menu
3. Click **API Setup**
4. You'll see:
   - **Phone Number ID** (looks like: 123456789012345)
   - **Access Token** (long string starting with EAA...)
5. Copy both values

### Step 2: Run Setup
```bash
cd /home/user/emr
python setup_whatsapp.py
```

### Step 3: Configure Credentials
1. Launch DocAssist EMR
2. Go to **Settings**
3. Click **WhatsApp** tab
4. Enter your **Phone Number ID**
5. Enter your **Access Token**
6. **Uncheck** "Mock Mode"
7. Check **"Enable WhatsApp Features"**
8. Click **"Test Connection"**
9. Click **Save Settings**

### Step 4: Test It
1. Open a patient record
2. Enter **your own phone number** in the patient's phone field
3. Create a prescription
4. Click **"Share WhatsApp"** button
5. Click **"Send Message"**
6. Check your phone - you'll receive the WhatsApp message!

---

## Features You Can Use

### 1. Send Individual Messages
- Click **"Share WhatsApp"** on any prescription
- Choose: Text, Template, or Prescription PDF
- Preview before sending
- Get delivery status

### 2. Use Message Templates
- Pre-approved message templates
- Appointment reminders
- Prescription ready notifications
- Follow-up reminders
- Lab results ready

### 3. Schedule Appointment Reminders
- Bulk schedule for all appointments
- Choose timing (2 hours to 3 days before)
- Automatic sending at scheduled time
- Track sent vs pending

### 4. View Conversations
- WhatsApp-style chat interface
- Message history
- Typing indicators
- Read receipts
- Quick replies in English & Hindi

---

## Troubleshooting

### "WhatsApp tab not showing in Settings"
You need to add it to the settings dialog. See `INTEGRATION_GUIDE.md` for instructions.

### "Messages not appearing in console" (Mock Mode)
Check that:
- Mock mode is enabled
- WhatsApp features are enabled
- You clicked "Save Settings"
- You're looking at the right console/terminal

### "Connection test failing" (Production Mode)
Check that:
- Phone Number ID is correct (no spaces)
- Access Token is correct (entire string)
- You have internet connection
- Credentials haven't expired in Meta Business Suite

### "Message sent but not received" (Production Mode)
Check that:
- Phone number is in E.164 format (+919876543210)
- Phone number is registered on WhatsApp
- You're using approved templates (for template messages)
- You haven't exceeded rate limits (20/minute)

---

## What Gets Installed

When you run `setup_whatsapp.py`:

1. **Database Tables:**
   - `whatsapp_conversations` - Stores conversation metadata
   - `whatsapp_messages` - Stores message history
   - `whatsapp_escalations` - Tracks urgent messages

2. **Settings File:**
   - `data/whatsapp_settings.json` - Stores your credentials (created on first save)

3. **Message Queue:**
   - Notification queue tables (if not already present)

---

## Common Use Cases

### Use Case: Daily Appointment Reminders
1. Every morning, open **Reminder Scheduler**
2. Click **"Schedule Reminders for All"**
3. Patients get reminders 1 day before their appointments
4. Reduces no-shows significantly

### Use Case: Share Prescription Instantly
1. Complete consultation
2. Generate prescription
3. Click **"Share WhatsApp"**
4. Patient receives prescription PDF on their phone
5. No need to print or email

### Use Case: Lab Results Ready
1. Lab results arrive
2. Open patient record
3. Click **"Share WhatsApp"**
4. Select template: **"Lab Results Ready"**
5. Patient gets notified to collect results

---

## Next Steps

1. **Test in Mock Mode First**
   - Get familiar with the interface
   - No risk of sending actual messages
   - Perfect for training staff

2. **Get WhatsApp Business Credentials**
   - Apply for WhatsApp Business API
   - Get credentials from Meta

3. **Switch to Production Mode**
   - Enter credentials
   - Test with your phone first
   - Then roll out to patients

4. **Customize Templates**
   - Submit custom templates to Meta for approval
   - Tailor messages to your clinic's voice

5. **Automate Reminders**
   - Set up daily reminder scheduling
   - Reduce administrative burden

---

## Support

- **Full Integration Guide:** `INTEGRATION_GUIDE.md`
- **Summary Document:** `/home/user/emr/WHATSAPP_INTEGRATION_SUMMARY.md`
- **Conversation UI Docs:** `README.md` (in same folder)
- **Setup Script:** `/home/user/emr/setup_whatsapp.py`

---

## Safety Features

✅ **Mock Mode** - Test safely without sending real messages
✅ **Message Preview** - See exactly what will be sent
✅ **Phone Validation** - Prevents invalid numbers
✅ **Rate Limiting** - Respects WhatsApp's 20 messages/minute limit
✅ **Retry Logic** - Automatically retries failed messages
✅ **Audit Trail** - All messages logged in database
✅ **Secure Storage** - Credentials encrypted and never logged

---

**Ready to get started?** Run `python setup_whatsapp.py` and follow the prompts!
