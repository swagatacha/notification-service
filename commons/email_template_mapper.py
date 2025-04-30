class EmailTemplateMapper:

    def __init__(self):
        self.header = '''
            <!doctype html>
            <html>
            <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
            </head>
            <body>
        '''
        self.footer ='''
            <br/>
            <p>Thank you </p>
            </body>
            </html>
        '''

    def buildhtml(self, mail_content):
        tmplate = ""
        tmplate += self.header + mail_content + self.footer
        return tmplate

