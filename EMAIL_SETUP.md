# PoolGuyz enquiry email setup

The contact form sends each enquiry to `bstartup92@gmail.com` after these
Render environment variables are set:

| Name | Value |
| --- | --- |
| `SMTP_USERNAME` | `bstartup92@gmail.com` |
| `SMTP_PASSWORD` | A Google App Password (not the normal Gmail password) |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `465` |
| `CONTACT_RECIPIENT` | `bstartup92@gmail.com` |

To create the App Password, enable two-step verification on the Gmail account,
then visit Google Account > Security > App passwords. Create an app password
named `PoolGuyz website` and paste the generated value into Render as
`SMTP_PASSWORD`.

Keep the App Password private. Never add it to GitHub or any project file.
