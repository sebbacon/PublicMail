
from south.db import db
from django.db import models
from mail.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'ProxyEmail'
        db.create_table('mail_proxyemail', (
            ('proxy_email', orm['mail.ProxyEmail:proxy_email']),
        ))
        db.send_create_signal('mail', ['ProxyEmail'])
        
        # Adding model 'Organisation'
        db.create_table('mail_organisation', (
            ('id', orm['mail.Organisation:id']),
            ('name', orm['mail.Organisation:name']),
        ))
        db.send_create_signal('mail', ['Organisation'])
        
        # Adding model 'CustomUser'
        db.create_table('mail_customuser', (
            ('user_ptr', orm['mail.CustomUser:user_ptr']),
            ('proxy_email', orm['mail.CustomUser:proxy_email']),
            ('organisation', orm['mail.CustomUser:organisation']),
            ('needs_moderation', orm['mail.CustomUser:needs_moderation']),
        ))
        db.send_create_signal('mail', ['CustomUser'])
        
        # Adding model 'Mail'
        db.create_table('mail_mail', (
            ('id', orm['mail.Mail:id']),
            ('subject', orm['mail.Mail:subject']),
            ('mfrom', orm['mail.Mail:mfrom']),
            ('mto', orm['mail.Mail:mto']),
            ('message', orm['mail.Mail:message']),
            ('in_reply_to', orm['mail.Mail:in_reply_to']),
            ('previewed', orm['mail.Mail:previewed']),
            ('approved', orm['mail.Mail:approved']),
            ('created', orm['mail.Mail:created']),
            ('sent', orm['mail.Mail:sent']),
            ('message_id', orm['mail.Mail:message_id']),
        ))
        db.send_create_signal('mail', ['Mail'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'ProxyEmail'
        db.delete_table('mail_proxyemail')
        
        # Deleting model 'Organisation'
        db.delete_table('mail_organisation')
        
        # Deleting model 'CustomUser'
        db.delete_table('mail_customuser')
        
        # Deleting model 'Mail'
        db.delete_table('mail_mail')
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'mail.customuser': {
            'needs_moderation': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mail.Organisation']", 'null': 'True', 'blank': 'True'}),
            'proxy_email': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mail.ProxyEmail']"}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'mail.mail': {
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_reply_to': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['mail.Mail']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'message_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'mfrom': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'mfrom'", 'to': "orm['mail.CustomUser']"}),
            'mto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'mto'", 'to': "orm['mail.CustomUser']"}),
            'previewed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '120'})
        },
        'mail.organisation': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'unique': 'True'})
        },
        'mail.proxyemail': {
            'proxy_email': ('django.db.models.fields.CharField', [], {'max_length': '10', 'primary_key': 'True'})
        }
    }
    
    complete_apps = ['mail']
