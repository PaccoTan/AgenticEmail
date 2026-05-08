import send_email
import display_email
from get_email import get_contacts

args = {'to': ['2211awesomeness@gmail.com'], 'subject': 'Sharing OWASP Top 10 for 2025 and RL Grid World', 'body': 'Hi there!\n\nI hope this message finds you well. \n\nI wanted to share two interesting files with you:\n\n1. **RL Grid World:** An image depicting a grid world, which is a concept used extensively in reinforcement learning (RL) tasks. This representation helps visualize the state space and actions in RL environments.\n\n2. **OWASP Top 10 for 2025:** A PDF document outlining the top security vulnerabilities to watch for in 2025 as compiled by OWASP (Open Web Application Security Project). This is essential reading for anyone involved in web security.\n\nPlease see the attached files for more details.\n\nBest regards,\nPacco Tan', 'cc': [], 'bcc': [], 'attachments': [{'filepath': '/uploads/temp.PNG', 'filename': 'temp.PNG'}, {'filepath': '/uploads/LLMAll_en-US_FINAL.pdf', 'filename': 'LLMAll_en-US_FINAL.pdf'}]}
msg, recipients = send_email.generate_msg(**args)
# send_email.send_msg(msg,recipients)
# msg, recipients = email_test.generate_msg(
#     to = ["example@email.com", "example@nonexistent-domain-test.com"],
#     subject = "Test Email",
#     body = "Hey. How are you doing?",
#     attachments=[
#         ("3dshapes.gif", "shapes.gif"),
#         ("Tan_Pacco_MidtermProposal.pdf", "proposal.pdf")
#     ]
# )
