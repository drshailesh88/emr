"""
Example usage of DocAssist Communication Services.

This demonstrates how to use the reminder, broadcast, notification queue,
and template manager services for automated patient communication.
"""

import asyncio
from datetime import datetime, date, timedelta
from src.services.communications import (
    ReminderService,
    BroadcastService,
    NotificationQueue,
    TemplateManager,
    Notification,
    NotificationPriority,
    Campaign,
    Segment
)


def demo_template_manager():
    """Demonstrate template manager usage."""
    print("\n=== Template Manager Demo ===\n")

    tm = TemplateManager()

    # Get and render appointment reminder template
    variables = {
        "patient_name": "Ram Lal",
        "doctor_name": "Dr. Sharma",
        "clinic_name": "DocAssist Clinic",
        "date": "15-Jan-2024",
        "time": "10:00 AM"
    }

    # English message
    message_en = tm.render("appointment_reminder", variables, language="en")
    print(f"English Message:\n{message_en}\n")

    # Hindi message
    message_hi = tm.render("appointment_reminder", variables, language="hi")
    print(f"Hindi Message:\n{message_hi}\n")

    # Create custom template
    tm.create_custom_template(
        "welcome_new_patient",
        "Welcome {patient_name} to {clinic_name}! We're here to serve you.",
        "स्वागत है {patient_name} {clinic_name} में! हम आपकी सेवा के लिए यहां हैं।",
        ["patient_name", "clinic_name"]
    )

    welcome_msg = tm.render("welcome_new_patient", {
        "patient_name": "Priya Sharma",
        "clinic_name": "DocAssist Clinic"
    })
    print(f"Custom Template:\n{welcome_msg}\n")


def demo_reminder_service():
    """Demonstrate reminder service usage."""
    print("\n=== Reminder Service Demo ===\n")

    rs = ReminderService()

    # 1. Schedule appointment reminders
    appointment = {
        "id": 123,
        "patient_id": 45,
        "doctor_name": "Dr. Sharma",
        "appointment_time": datetime.now() + timedelta(days=2, hours=10),
        "clinic_name": "DocAssist Clinic",
        "clinic_phone": "9876543210"
    }

    reminder_ids = rs.schedule_appointment_reminder(appointment)
    print(f"✓ Scheduled {len(reminder_ids)} appointment reminders")

    # 2. Schedule follow-up reminder
    visit = {
        "patient_id": 45,
        "follow_up_date": date.today() + timedelta(days=14),
        "doctor_name": "Dr. Sharma",
        "clinic_phone": "9876543210"
    }

    follow_up_id = rs.schedule_follow_up_reminder(visit)
    print(f"✓ Scheduled follow-up reminder: {follow_up_id}")

    # 3. Schedule medication reminders
    prescription = {
        "medications": [
            {
                "drug_name": "Metformin",
                "dose": "500mg",
                "frequency": "BD",
                "duration": "30 days",
                "instructions": "after meals"
            }
        ]
    }

    patient = {"id": 45, "name": "Ram Lal"}
    med_reminder_ids = rs.schedule_medication_reminders(prescription, patient)
    print(f"✓ Scheduled {len(med_reminder_ids)} medication reminders")

    # 4. Schedule preventive care
    patient_full = {
        "id": 45,
        "age": 65,
        "gender": "M",
        "chronic_conditions": ["diabetes", "hypertension"]
    }

    preventive_ids = rs.schedule_preventive_care(patient_full)
    print(f"✓ Scheduled {len(preventive_ids)} preventive care reminders")

    # 5. Schedule lab due reminder
    lab_id = rs.schedule_lab_due_reminder(
        patient,
        "HbA1c",
        date.today() + timedelta(days=90)
    )
    print(f"✓ Scheduled lab reminder: {lab_id}")

    # 6. Get pending reminders for patient
    pending_reminders = rs.get_pending_reminders(45)
    print(f"\n✓ Patient has {len(pending_reminders)} pending reminders:")
    for reminder in pending_reminders[:3]:  # Show first 3
        print(f"  - {reminder.type.value}: {reminder.scheduled_time.strftime('%Y-%m-%d %H:%M')}")


def demo_broadcast_service():
    """Demonstrate broadcast service usage."""
    print("\n=== Broadcast Service Demo ===\n")

    bs = BroadcastService()

    # 1. Create patient segment
    segment = bs.create_patient_segment(
        "Diabetic Patients 40+",
        {
            "diagnosis": "diabetes",
            "age_range": [40, 100]
        }
    )
    print(f"✓ Created segment '{segment.name}' with {segment.patient_count} patients")

    # 2. Send clinic notice
    # In a real scenario, you'd get actual patient IDs from database
    patient_ids = [1, 2, 3, 4, 5]  # Example patient IDs
    notice_msg = "Our clinic will be closed on 26-Jan for Republic Day. Emergency calls: 9876543210"

    broadcast_id = bs.send_clinic_notice(
        patient_ids,
        notice_msg,
        name="Republic Day Closure Notice"
    )
    print(f"✓ Sent clinic notice to {len(patient_ids)} patients: {broadcast_id}")

    # 3. Send health tip
    tip = "Drink at least 8 glasses of water daily. Proper hydration helps regulate blood sugar levels."
    tip_id = bs.send_health_tip("diabetics", tip)
    print(f"✓ Sent health tip to diabetic patients: {tip_id}")

    # 4. Send campaign
    campaign = Campaign(
        name="Free Diabetes Screening Camp",
        description="Community health camp",
        message="Join our FREE Diabetes Screening Camp on 20-Jan! Get your blood sugar, HbA1c checked. Call 9876543210 to register.",
        segment_id=segment.id,
        scheduled_time=datetime.now() + timedelta(hours=2)
    )

    campaign_id = bs.send_campaign(campaign)
    print(f"✓ Scheduled campaign: {campaign_id}")

    # 5. Get delivery stats
    stats = bs.get_delivery_stats(broadcast_id)
    if stats:
        print(f"\n✓ Delivery Stats for {broadcast_id}:")
        print(f"  Total: {stats.total}, Pending: {stats.pending}")


def demo_notification_queue():
    """Demonstrate notification queue usage."""
    print("\n=== Notification Queue Demo ===\n")

    nq = NotificationQueue()

    # 1. Enqueue notifications
    notifications = [
        Notification(
            patient_id=45,
            phone="9876543210",
            message="Your appointment is tomorrow at 10 AM",
            priority=NotificationPriority.HIGH,
            channel="whatsapp"
        ),
        Notification(
            patient_id=46,
            phone="9876543211",
            message="Time to take your medication",
            priority=NotificationPriority.NORMAL,
            channel="whatsapp"
        ),
        Notification(
            patient_id=47,
            phone="9876543212",
            message="URGENT: Your test results are ready",
            priority=NotificationPriority.URGENT,
            channel="whatsapp"
        )
    ]

    for notif in notifications:
        notif_id = nq.enqueue(notif)
        print(f"✓ Enqueued notification: {notif_id} (priority: {notif.priority.value})")

    # 2. Get queue status
    status = nq.get_queue_status()
    print(f"\n✓ Queue Status:")
    print(f"  Pending: {status.pending}")
    print(f"  Processing: {status.processing}")
    print(f"  Failed: {status.failed}")
    print(f"  Sent today: {status.sent_today}/{status.total_today}")


async def demo_process_queue():
    """Demonstrate queue processing (async)."""
    print("\n=== Process Notification Queue (Async) ===\n")

    nq = NotificationQueue()

    # Note: This requires WhatsApp credentials to be configured
    # In a real scenario, uncomment the following:
    #
    # stats = await nq.process_queue(max_batch_size=10)
    # print(f"✓ Processing complete:")
    # print(f"  Sent: {stats['sent']}")
    # print(f"  Failed: {stats['failed']}")
    # print(f"  Skipped: {stats['skipped']}")

    print("✓ Queue processing requires WhatsApp credentials")
    print("  Set WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN in .env")


def demo_integrated_workflow():
    """Demonstrate integrated workflow combining all services."""
    print("\n=== Integrated Workflow Demo ===\n")

    tm = TemplateManager()
    rs = ReminderService()
    nq = NotificationQueue()

    # Scenario: New appointment scheduled
    patient = {"id": 45, "name": "Ram Lal", "phone": "9876543210"}
    appointment_time = datetime.now() + timedelta(days=3, hours=10)

    # 1. Schedule reminders
    appointment = {
        "id": 123,
        "patient_id": patient["id"],
        "doctor_name": "Dr. Sharma",
        "appointment_time": appointment_time,
        "clinic_name": "DocAssist Clinic",
        "clinic_phone": "9876543210"
    }

    reminder_ids = rs.schedule_appointment_reminder(appointment)
    print(f"✓ Scheduled appointment reminders: {reminder_ids}")

    # 2. Generate confirmation message from template
    variables = {
        "patient_name": patient["name"],
        "doctor_name": "Dr. Sharma",
        "clinic_name": "DocAssist Clinic",
        "date": appointment_time.strftime("%d-%b-%Y"),
        "time": appointment_time.strftime("%I:%M %p")
    }

    message = tm.render("appointment_reminder", variables, language="en")

    # 3. Queue immediate confirmation
    confirmation = Notification(
        patient_id=patient["id"],
        phone=patient["phone"],
        message=message,
        priority=NotificationPriority.HIGH,
        channel="whatsapp",
        metadata={"type": "appointment_confirmation", "appointment_id": 123}
    )

    notif_id = nq.enqueue(confirmation)
    print(f"✓ Queued appointment confirmation: {notif_id}")
    print(f"\n✓ Complete workflow executed successfully!")


def main():
    """Run all demos."""
    print("=" * 60)
    print("DocAssist Communication Services - Demo")
    print("=" * 60)

    try:
        demo_template_manager()
        demo_reminder_service()
        demo_broadcast_service()
        demo_notification_queue()
        demo_integrated_workflow()

        # Async demo
        print("\n" + "=" * 60)
        asyncio.run(demo_process_queue())

        print("\n" + "=" * 60)
        print("✅ All demos completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
