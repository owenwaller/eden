# -*- coding: utf-8 -*-

# Populate default roles and permissions

# Set deployment_settings.base.prepopulate to 0 in Production
# (to save 1x DAL hit every page).
pop_list = deployment_settings.get_base_prepopulate()
if pop_list == 0:
    pop_list = []
else:
    table = db[auth.settings.table_group_name]
    # The query used here takes 2/3 the time of .count().
    if db(table.id > 0).select(table.id, limitby=(0, 1)).first():
        pop_list = []
    if not isinstance(pop_list, (list, tuple)):
        pop_list = [pop_list]
# Add core roles as long as at least one populate setting is on
if len(pop_list) > 0:

    # Create the bulk Importer object
    bi = s3base.S3BulkImporter()

    response.s3.import_role = bi.import_role

    # Shortcuts
    acl = auth.permission
    sysroles = auth.S3_SYSTEM_ROLES
    create_role = auth.s3_create_role
    update_acls = auth.s3_update_acls

    default_oacl = acl.READ|acl.UPDATE

    # Do not remove or change order of these 5 definitions (System Roles):
    create_role("Administrator",
                "System Administrator - can access & make changes to any data",
                uid=sysroles.ADMIN,
                system=True, protected=True)
    authenticated = create_role("Authenticated",
                                "Authenticated - all logged-in users",
                                # Authenticated users can see the Map
                                dict(c="gis", uacl=acl.ALL, oacl=acl.ALL),
                                # Note the owning role for locations is set to Authenticated
                                # by default, so this controls the access that logged in
                                # users have. (In general, tables do not have a default
                                # owning role.)
                                dict(c="gis", f="location", uacl=acl.READ|acl.CREATE, oacl=acl.ALL),
                                # Authenticated users can only see/edit their own PR records
                                dict(c="pr", uacl=acl.NONE, oacl=acl.READ|acl.UPDATE),
                                dict(t="pr_person", uacl=acl.NONE, oacl=acl.READ|acl.UPDATE),
                                # But need to be able to add/edit addresses
                                dict(c="pr", f="person", uacl=acl.CREATE, oacl=acl.READ|acl.UPDATE),
                                # And access the Autocompletes
                                dict(c="pr", f="person_search", uacl=acl.READ),
                                dict(c="pr", f="pentity", uacl=acl.READ),
                                dict(c="msg", f="search", uacl=acl.READ),
                                # Authenticated  users can see the Supply Catalogue
                                dict(c="supply", uacl=acl.READ|acl.CREATE, oacl=default_oacl),
                                uid=sysroles.AUTHENTICATED,
                                protected=True)
    # Authenticated users:
    # Have access to all Orgs, Hospitals, Shelters
    update_acls(authenticated,
                dict(c="org", uacl=acl.READ|acl.CREATE, oacl=default_oacl),
                # Since we specify a Table ACL for Anonymous, we also need 1 for Authenticated
                dict(t="org_organisation", uacl=acl.READ|acl.CREATE, oacl=default_oacl),
                dict(c="hms", uacl=acl.READ|acl.CREATE, oacl=default_oacl),
                dict(c="cr", uacl=acl.READ|acl.CREATE, oacl=default_oacl)
                )

    # If we don't have OrgAuth active, then Authenticated users:
    # Have access to all Orgs, Sites & the Inventory & Requests thereof
    update_acls(authenticated,
                dict(c="asset", uacl=acl.READ|acl.CREATE, oacl=default_oacl),
                dict(c="inv", uacl=acl.READ|acl.CREATE, oacl=default_oacl),
                dict(c="req", uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=default_oacl),
                # Allow authenticated users to view the Certificate Catalog
                dict(t="hrm_certificate", uacl=acl.READ),
                # HRM access is controlled to just HR Staff, except for:
                # Access to your own record & to be able to search for Skills
                # requires security policy 4+
                dict(c="hrm", uacl=acl.NONE, oacl=acl.READ|acl.UPDATE),
                dict(c="hrm", f="staff", uacl=acl.NONE, oacl=acl.NONE),
                dict(c="hrm", f="volunteer", uacl=acl.NONE, oacl=acl.NONE),
                dict(c="hrm", f="person", uacl=acl.NONE, oacl=acl.READ|acl.UPDATE),
                dict(c="hrm", f="skill", uacl=acl.READ, oacl=acl.READ)
                )

    create_role("Anonymous",
                "Unauthenticated users",

                # Defaults for Trunk
                dict(c="org", uacl=acl.READ, oacl=default_oacl),
                dict(c="project", uacl=acl.READ, oacl=default_oacl),
                dict(c="cr", uacl=acl.READ, oacl=default_oacl),
                dict(c="hms", uacl=acl.READ, oacl=default_oacl),
                #dict(c="inv", uacl=acl.READ, oacl=default_oacl),
                dict(c="supply", uacl=acl.READ, oacl=default_oacl),
                dict(c="delphi", uacl=acl.READ, oacl=default_oacl),

                # Allow unauthenticated users to view the list of organisations
                # so they can select an organisation when registering
                dict(t="org_organisation", uacl=acl.READ, entity="any"),
                # Allow unauthenticated users to view the Map
                dict(c="gis", uacl=acl.READ, oacl=default_oacl),
                # Allow unauthenticated users to cache Map feeds
                dict(c="gis", f="cache_feed", uacl=acl.ALL, oacl=default_oacl),
                # Allow unauthenticated users to view feature queries
                dict(c="gis", f="feature_query", uacl=acl.NONE, oacl=default_oacl),
                uid=sysroles.ANONYMOUS,
                protected=True)

    # Primarily for Security Policy 2
    create_role("Editor",
                "Editor - can access & make changes to any unprotected data",
                uid=sysroles.EDITOR,
                system=True, protected=True)

    # MapAdmin
    create_role("MapAdmin",
                "MapAdmin - allowed access to edit the MapService Catalogue",
                dict(c="gis", uacl=acl.ALL, oacl=acl.ALL),
                dict(c="gis", f="location", uacl=acl.ALL, oacl=acl.ALL),
                uid=sysroles.MAP_ADMIN,
                system=True, protected=True)

    # OrgAdmin (policies 6, 7 and 8)
    create_role("OrgAdmin",
                "OrgAdmin - allowed to manage user roles for entity realms",
                uid=sysroles.ORG_ADMIN,
                system=True, protected=True)

# Enable shortcuts (needed by default.py)
system_roles = auth.get_system_roles()
ADMIN = system_roles.ADMIN
AUTHENTICATED = system_roles.AUTHENTICATED
ANONYMOUS = system_roles.ANONYMOUS
EDITOR = system_roles.EDITOR
MAP_ADMIN = system_roles.MAP_ADMIN
ORG_ADMIN = system_roles.ORG_ADMIN

# END =========================================================================
