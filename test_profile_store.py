"""
KAIA – Profile Store quick test.
Run: python test_profile_store.py
"""

from core import ProfileStore, NeuroadaptiveMode

store = ProfileStore()

print("── Creating profile ──────────────────────────────")
profile = store.create_profile(
    name="Test User",
    context="Preparing for the data science final exam",
)
print(f"Created:  {profile.user_id}")
print(f"Name:     {profile.name}")
print(f"Context:  {profile.context}")

print("\n── Updating neuroadaptive mode ───────────────────")
store.update_mode(profile, NeuroadaptiveMode.FLOW)
print(f"Mode:     {profile.current_mode}")

print("\n── Updating personality traits ───────────────────")
store.update_trait(profile, "openness", 0.8)
store.update_trait(profile, "perfectionism", 0.7)
print(f"Traits:   {profile.traits}")

print("\n── Starting a session ────────────────────────────")
session = store.start_session(profile, provider="claude", model="claude-sonnet-4-20250514")
print(f"Session:  {session.session_id}")

store.add_message(session, "user", "I don't understand gradient descent.", tokens=12)
store.add_message(session, "assistant", "Let's explore that together.", tokens=8, latency_ms=430)

print(f"Messages: {session.message_count}")
print(f"Tokens:   {session.total_tokens}")
print(f"Latency:  {session.avg_latency_ms} ms avg")

print("\n── Closing session ───────────────────────────────")
store.close_session(session, profile)
print(f"Ended at: {session.ended_at}")

print("\n── Reloading profile from disk ───────────────────")
reloaded = store.load_profile(profile.user_id)
print(f"Sessions: {reloaded.session_count}")
print(f"Messages: {reloaded.total_messages}")
print(f"Traits:   {reloaded.traits}")

print("\n── All profiles ──────────────────────────────────")
for p in store.list_profiles():
    print(p)

print("\nProfile Store test complete.")
