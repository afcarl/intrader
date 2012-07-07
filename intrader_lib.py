""" Helper functions for using Intrader """

import logging
from mongolog.handlers import MongoHandler
from logging.handlers import SMTPHandler
import ConfigParser

def initLogger(log_name, log_level, email = True):
    """ Creates logger instance with MongoHandler """
    log = logging.getLogger(log_name)
    if 'debug' in log_level.lower():
        log.setLevel(logging.DEBUG)
    elif 'warn' in log_level.lower():
        log.setLevel(logging.WARNING)
    elif 'error' in log_level.lower():
        log.setLevel(logging.ERROR)
    elif 'crit' in log_level.lower():
        log.setLevel(logging.CRITICAL)
    
    log.addHandler(MongoHandler.to(db='logs', collection='intrader'))
    if email:
        u, p = get_gmail_auth()
        log.addHandler(TlsSMTPHandler(('smtp.gmail.com', 587),
                                      u,
                                      [u],
                                      'Intrader Error',
                                      (u, p)))

    return log

def get_gmail_auth():
    
    config = ConfigParser.ConfigParser()
    config.read('intrader.conf')

    return (config.get('Gmail', 'username'),
            config.get('Gmail', 'password'))

class TlsSMTPHandler(logging.handlers.SMTPHandler):
    def emit(self, record):
        """
        Emit a record.
 
        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            import string # for tls add this line
            try:
                from email.utils import formatdate
            except ImportError:
                formatdate = self.date_time
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            string.join(self.toaddrs, ","),
                            self.getSubject(record),
                            formatdate(), msg)
            if self.username:
                smtp.ehlo() # for tls add this line
                smtp.starttls() # for tls add this line
                smtp.ehlo() # for tls add this line
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)    

