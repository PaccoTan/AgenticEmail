from weasyprint import HTML

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Letter of Recommendation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 60px;
            color: #000;
        }
        .header {
            margin-bottom: 40px;
        }
        .date {
            margin-bottom: 20px;
        }
        .recipient {
            margin-bottom: 20px;
        }
        .content {
            margin-bottom: 30px;
        }
        .closing {
            margin-top: 40px;
        }
    </style>
</head>
<body>

    <div class="header">
        <strong>Your Name</strong><br>
        Your Title / Position<br>
        Your Institution<br>
        Your Email<br>
        Your Phone Number
    </div>

    <div class="date">
        April 24, 2026
    </div>

    <div class="recipient">
        Admissions Committee<br>
        Louisiana State University
    </div>

    <div class="content">
        Dear Admissions Committee,
        <br><br>
        I am pleased to write this letter of recommendation for John Smith, who is applying for admission to Louisiana State University to pursue a degree in Computer Science.
        <br><br>
        John is a highly intelligent and hardworking student who consistently demonstrates a strong commitment to his academic goals. Throughout his time in my class, he has shown excellent problem-solving abilities, a keen interest in learning, and the determination to succeed even when faced with challenging material.
        <br><br>
        In addition to his academic strengths, John is responsible, respectful, and collaborative. He contributes positively to the classroom environment and is always willing to assist his peers. His work ethic and intellectual curiosity make him well-suited for the rigors of a Computer Science program.
        <br><br>
        I am confident that John Smith will be a valuable addition to your academic community at Louisiana State University. I strongly recommend him for admission without reservation.
    </div>

    <div class="closing">
        Sincerely,<br><br>
        Your Name
    </div>

</body>
</html>
"""

HTML(string=html_content).write_pdf('output.pdf')