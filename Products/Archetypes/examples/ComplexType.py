from Products.Archetypes.public import *
from Products.Archetypes import Field

fields = ['ObjectField', 'StringField', 'MetadataField',
          'FileField', 'TextField', 'DateTimeField', 'LinesField',
          'IntegerField', 'FloatField', 'FixedPointField',
          'BooleanField',
          # 'ReferenceField', 'ComputedField', 'CMFObjectField', 'ImageField'
          ]

field_instances = []

for f in fields:
    field_instances.append(getattr(Field, f)(f.lower()))

schema = Schema(tuple(field_instances) + (
    LinesField('selectionlinesfield1',
               vocabulary='_get_selection_vocab',
               enforceVocabulary=1,
               widget=SelectionWidget(label='Selection'),
               ),
    LinesField('selectionlinesfield2',
               vocabulary='_get_selection_vocab',
               widget=SelectionWidget(label='Selection'),
               ),
    ))

class ComplexType(BaseContent):
    """A simple archetype"""
    schema = schema

    def _get_selection_vocab(self):
        return DisplayList((('Test','Test'),))

registerType(ComplexType)
