# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################

from Products.Archetypes.base.baseobject import BaseObject
from Products.Archetypes.base.extensiblemetadata import ExtensibleMetadata
from Products.Archetypes.interfaces.base import IBaseContent
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.metadata import IExtensibleMetadata
from Products.Archetypes.base.catalogmultiplex import CatalogMultiplex
from Products.Archetypes.lib.utils import shasattr

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.History import Historical
from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.PortalContent import PortalContent
from OFS.PropertyManager import PropertyManager
from ZODB.POSException import ConflictError
from Acquisition import aq_get

_marker = []

class BaseContentMixin(CatalogMultiplex,
                    BaseObject,
                    PortalContent,
                    Historical):
    """A not-so-basic CMF Content implementation that doesn't
    include Dublin Core Metadata"""

    __implements__ = IBaseContent, IReferenceable, PortalContent.__implements__

    isPrincipiaFolderish=0
    manage_options = PortalContent.manage_options + Historical.manage_options

    security = ClassSecurityInfo()

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        BaseObject.manage_afterAdd(self, item, container)
        CatalogMultiplex.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        BaseObject.manage_afterClone(self, item)
        CatalogMultiplex.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        BaseObject.manage_beforeDelete(self, item, container)
        CatalogMultiplex.manage_beforeDelete(self, item, container)

        #and reset the rename flag (set in Referenceable._notifyCopyOfCopyTo)
        self._at_cp_refs = None

    def _notifyOfCopyTo(self, container, op=0):
        """OFS.CopySupport notify
        """
        BaseObject._notifyOfCopyTo(self, container, op=op)
        PortalContent._notifyOfCopyTo(self, container, op=op)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'PUT')
    def PUT(self, REQUEST=None, RESPONSE=None):
        """ HTTP PUT handler with marshalling support """
        if not REQUEST:
            REQUEST = self.REQUEST
        if not RESPONSE:
            RESPONSE = REQUEST.RESPONSE
        if not self.Schema().hasLayer('marshall'):
            RESPONSE.setStatus(501) # Not implemented
            return RESPONSE

        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)

        file = REQUEST.get('BODYFILE', _marker)
        if file is _marker:
            data = REQUEST.get('BODY', _marker)
            if data is _marker:
                raise AttributeError, 'REQUEST neither has a BODY nor a BODYFILE'
        else:
            data = file.read()
            file.seek(0)

        # XXX should we maybe not accept PUT requests without a
        # content type?
        mimetype = REQUEST.get_header('content-type', None)

        try:
            filename = REQUEST._steps[-2] #XXX fixme, use a real name
        except ConflictError:
            raise
        except:
            filename = (getattr(file, 'filename', None) or
                        getattr(file, 'name', None))

        # XXX remove after we are using global services
        # use the request to find an object in the traversal hirachie that is
        # able to acquire a mimetypes_registry instance
        # This is a hack to avoid the acquisition problem on FTP/WebDAV object
        # creation
        parents = REQUEST.get('PARENTS', None)
        context = None
        if parents is not None:
            for parent in parents:
                if aq_get(parent, 'mimetypes_registry', None, 1) is not None:
                    context = parent
                    break

        # Marshall the data
        marshaller = self.Schema().getLayerImpl('marshall')
        ddata = marshaller.demarshall(self, data,
                                      mimetype=mimetype,
                                      filename=filename,
                                      REQUEST=REQUEST,
                                      RESPONSE=RESPONSE,
                                      context=context)
        if shasattr(self, 'demarshall_hook') \
           and self.demarshall_hook:
            self.demarshall_hook(ddata)

        self.reindexObject()
        RESPONSE.setStatus(204)
        return RESPONSE


    security.declareProtected(CMFCorePermissions.View, 'manage_FTPget')
    def manage_FTPget(self, REQUEST=None, RESPONSE=None):
        "Get the raw content for this object (also used for the WebDAV SRC)"

        if REQUEST is None:
            REQUEST = self.REQUEST

        if RESPONSE is None:
            RESPONSE = REQUEST.RESPONSE

        if not self.Schema().hasLayer('marshall'):
            RESPONSE.setStatus(501) # Not implemented
            return RESPONSE

        marshaller = self.Schema().getLayerImpl('marshall')
        ddata = marshaller.marshall(self, REQUEST=REQUEST, RESPONSE=RESPONSE)
        if shasattr(self, 'marshall_hook') \
           and self.marshall_hook:
            ddata = self.marshall_hook(ddata)

        content_type, length, data = ddata

        RESPONSE.setHeader('Content-Type', content_type)
        RESPONSE.setHeader('Content-Length', length)

        if isinstance(data, basestring):
            return data

        while data is not None:
            RESPONSE.write(data.data)
            data=data.next

InitializeClass(BaseContentMixin)

class BaseContent(BaseContentMixin,
                  ExtensibleMetadata,
                  PropertyManager):
    """A not-so-basic CMF Content implementation with Dublin Core
    Metadata included"""

    __implements__ = BaseContentMixin.__implements__, IExtensibleMetadata

    schema = BaseContentMixin.schema + ExtensibleMetadata.schema

    manage_options = BaseContentMixin.manage_options + \
        PropertyManager.manage_options

    def __init__(self, oid, **kwargs):
        BaseContentMixin.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

InitializeClass(BaseContent)


BaseSchema = BaseContent.schema

__all__ = ('BaseContent', 'BaseContentMixin', 'BaseSchema', )
