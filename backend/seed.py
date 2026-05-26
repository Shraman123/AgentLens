"""
Seed script — populate demo conversations to test the dashboard.
Run: python seed.py
"""
import httpx
import random
import time

API_URL = "http://localhost:8000"
API_KEY = "ak_demo_123456789"
HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}

conversations = [
    ("How do I reset my password?", "You can reset your password by clicking 'Forgot Password' on the login page."),
    ("I want a refund for my last order", "I'm sorry, I'm not able to process refunds directly. Please contact support@company.com."),
    ("What's the price of the Pro plan?", "The Pro plan is $49/month and includes unlimited API calls."),
    ("Can you book a flight for me?", "I'm sorry, I'm not able to book flights. I can only answer questions about our product."),
    ("How do I integrate your API?", "Check out our docs at docs.company.com. Here's a quick start: pip install our-sdk"),
    ("This is completely broken, nothing works!", "I'm sorry to hear that. Can you describe what issue you're experiencing?"),
    ("What's the difference between Free and Pro?", "Free tier: 1000 calls/month. Pro: unlimited calls + priority support."),
    ("My payment failed", "I cannot process payments. Please contact billing@company.com or try again with a different card."),
    ("How do I cancel my subscription?", "You can cancel anytime from Settings > Billing > Cancel Subscription."),
    ("Can you write code for me?", "I'm a support assistant, not a coding assistant. I can help with questions about our product."),
    ("Is there a free trial?", "Yes! We offer a 14-day free trial with full Pro features, no credit card required."),
    ("I've been waiting 3 days for a response from support", "I apologize for the delay. I'll escalate this issue immediately. Your ticket ID should be in your email."),
    ("What languages do you support?", "Our API supports Python, JavaScript, Go, Ruby, and Java with official SDKs."),
    ("How many API calls can I make per minute?", "Rate limits: Free = 10/min, Pro = 100/min, Enterprise = unlimited."),
    ("Your app is down", "I'm unable to check system status directly. Please check status.company.com for real-time updates."),
    ("How do I add team members?", "Go to Settings > Team > Invite Members and enter their email addresses."),
    ("I love the new dashboard update!", "Thank you so much! We're glad you're enjoying it. Let us know if you have any feedback."),
    ("Where is my data stored?", "All data is stored in US-East AWS data centers with encryption at rest and in transit."),
    ("Can I export my data?", "Yes, go to Settings > Data > Export to download a CSV or JSON export of all your data."),
    ("Do you have a Slack integration?", "Not yet, but it's on our roadmap! You can upvote it at feedback.company.com."),
]

print("Seeding conversations...")
for i, (user_msg, agent_resp) in enumerate(conversations):
    r = httpx.post(
        f"{API_URL}/log",
        headers=HEADERS,
        json={
            "user_message": user_msg,
            "agent_response": agent_resp,
            "session_id": f"session-{i % 5}",
            "metadata": {"source": "seed_script", "index": i}
        }
    )
    print(f"  [{i+1}/{len(conversations)}] {r.status_code} — {user_msg[:50]}")
    time.sleep(0.1)

print("\nDone! Now run analysis:")
print('  curl -X POST http://localhost:8000/analyze -H "x-api-key: ak_demo_123456789" -H "Content-Type: application/json" -d \'{"limit": 50}\'')
