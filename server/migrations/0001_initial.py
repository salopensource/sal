# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserProfile'
        db.create_table(u'server_userprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
        ))
        db.send_create_signal(u'server', ['UserProfile'])

        # Adding model 'BusinessUnit'
        db.create_table(u'server_businessunit', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal(u'server', ['BusinessUnit'])

        # Adding M2M table for field users on 'BusinessUnit'
        m2m_table_name = db.shorten_name(u'server_businessunit_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('businessunit', models.ForeignKey(orm[u'server.businessunit'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['businessunit_id', 'user_id'])

        # Adding model 'MachineGroup'
        db.create_table(u'server_machinegroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('business_unit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['server.BusinessUnit'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('manifest', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal(u'server', ['MachineGroup'])

        # Adding model 'Machine'
        db.create_table(u'server_machine', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('serial', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('operating_system', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('memory', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('munki_version', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('manifest', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('hd_space', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal(u'server', ['Machine'])


    def backwards(self, orm):
        # Deleting model 'UserProfile'
        db.delete_table(u'server_userprofile')

        # Deleting model 'BusinessUnit'
        db.delete_table(u'server_businessunit')

        # Removing M2M table for field users on 'BusinessUnit'
        db.delete_table(db.shorten_name(u'server_businessunit_users'))

        # Deleting model 'MachineGroup'
        db.delete_table(u'server_machinegroup')

        # Deleting model 'Machine'
        db.delete_table(u'server_machine')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'server.businessunit': {
            'Meta': {'object_name': 'BusinessUnit'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        },
        u'server.machine': {
            'Meta': {'object_name': 'Machine'},
            'hd_space': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manifest': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'memory': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'munki_version': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'operating_system': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'serial': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'server.machinegroup': {
            'Meta': {'object_name': 'MachineGroup'},
            'business_unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['server.BusinessUnit']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manifest': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'server.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['server']