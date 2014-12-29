# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'HueyQueue'
        db.create_table('huey_queue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'djhuey', ['HueyQueue'])

        # Adding model 'HueySchedule'
        db.create_table('huey_schedule', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.TextField')()),
            ('ts', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'djhuey', ['HueySchedule'])

        # Adding model 'HueyResult'
        db.create_table('huey_result', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('result', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'djhuey', ['HueyResult'])

        # Adding model 'HueyEvent'
        db.create_table('huey_event', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('channel', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'djhuey', ['HueyEvent'])


    def backwards(self, orm):
        # Deleting model 'HueyQueue'
        db.delete_table('huey_queue')

        # Deleting model 'HueySchedule'
        db.delete_table('huey_schedule')

        # Deleting model 'HueyResult'
        db.delete_table('huey_result')

        # Deleting model 'HueyEvent'
        db.delete_table('huey_event')


    models = {
        u'djhuey.hueyevent': {
            'Meta': {'object_name': 'HueyEvent', 'db_table': "'huey_event'"},
            'channel': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {})
        },
        u'djhuey.hueyqueue': {
            'Meta': {'object_name': 'HueyQueue', 'db_table': "'huey_queue'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.TextField', [], {})
        },
        u'djhuey.hueyresult': {
            'Meta': {'object_name': 'HueyResult', 'db_table': "'huey_result'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'result': ('django.db.models.fields.TextField', [], {})
        },
        u'djhuey.hueyschedule': {
            'Meta': {'object_name': 'HueySchedule', 'db_table': "'huey_schedule'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.TextField', [], {}),
            'ts': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        }
    }

    complete_apps = ['djhuey']