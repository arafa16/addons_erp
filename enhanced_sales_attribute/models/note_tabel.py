from odoo import models, fields, api

class NoteTable(models.Model):
    _name = 'enhanced.note.tabel'
    name = fields.Char(string='Judul')
    deskripsi = fields.Text(string='Deskripsi')