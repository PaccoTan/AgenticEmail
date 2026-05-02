import email_test
import display_email

args = {'to': ['tramanhtruong32@gmail.com'], 'subject': 'Difference Between Apples and Oranges', 'body': "Dear [Recipient's Name],\n\nI hope this message finds you well. I wanted to take a moment to inform you about the differences between apples and oranges, which are both popular fruits but possess distinct characteristics.\n\n1. **Taste**: Apples are generally sweet and can range from tart to mild flavors, while oranges are known for their citrusy and tangy taste.\n2. **Texture**: Apples have a crisp and firm texture, while oranges are juicy and have a softer skin.\n3. **Nutritional Content**: Both fruits offer different nutritional benefits; apples are rich in fiber, whereas oranges provide high amounts of vitamin C.\n4. **Culinary Uses**: Apples are often used in pies, salads, and sauces, whereas oranges are commonly consumed fresh or used in juices and desserts.\n\nIf you would like to know more or have any specific questions, feel free to ask.\n\nBest regards,\nPacco Tan", 'cc': [], 'bcc': [], 'attachments': []}

msg, recipients = email_test.generate_msg(**args)
email_test.send_msg(msg,recipients)
# msg, recipients = email_test.generate_msg(
#     to = ["example@email.com", "example@nonexistent-domain-test.com"],
#     subject = "Test Email",
#     body = "Hey. How are you doing?",
#     attachments=[
#         ("3dshapes.gif", "shapes.gif"),
#         ("Tan_Pacco_MidtermProposal.pdf", "proposal.pdf")
#     ]
# )
