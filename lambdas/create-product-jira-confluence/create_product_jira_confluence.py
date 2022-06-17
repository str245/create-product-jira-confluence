import sys
import json
import os
import time
import requests
from secret_helper import SecretHelper

URL = 'https://jira.company.com'  # URL de la instancia de JIRA Server

HOST_CONFLUENCE = 'https://confluence.company.com'  # URL de Confluence Cloud
ESPACIO_PLANTILLA = 'ENP'  # CLAVE del espacio a copiar cuando se crea un nuevo producto
ID_TEMPLATE_HOME = '0000001'  # ID de la homepage del espacio plantilla
ID_SERVICE_DESK_PROJECT = '0000002'
IDROL_ADMIN = '10002'
IDROL_DEV = '10001'
IDROL_SCRUM = '10402'
IDROL_AUDITOR = '10400'
IDROL_PRODUCTOWNER = '10401'
IDROL_SERVICEDESKTEAM = '10201'
ID_INSIGHT_OBJECT = '1'
ID_INSIGHT_OBJECT_NAME = '2'
ID_INSIGHT_OBJECT_NEGOCIO = '3'
ID_INSIGHT_OBJECT_NEGOCIO_NAME = '10'
ID_INSIGHT_OBJECT_KEY = '1'
ID_INSIGHT_OBJECT_RESP_NEGOCIO = '29'
ID_INSIGHT_OBJECT_RESP_NEGOCIO_CORREO = '30'
ID_INSIGHT_OBJECT_RESP_NEGOCIO_TELEFONO = '31'
ID_INSIGHT_OBJECT_RESP_OPERACION = '32'
ID_INSIGHT_OBJECT_RESP_OPERACION_CORREO = '33'
ID_INSIGHT_OBJECT_RESP_OPERACION_TELEFONO = '34'
ID_INSIGHT_OBJECT_RESP_DESARROLLO = '35'
ID_INSIGHT_OBJECT_RESP_DESARROLLO_CORREO = '36'
ID_INSIGHT_OBJECT_RESP_DESARROLLO_TELEFONO = '37'
ID_INSIGHT_OBJECT_NEGOCIO_ATTRIBUTE = '38'
ID_INSIGHT_OBJECT_PRODUCT_OWNER = '44'
ID_INSIGHT_OBJECT_PRODUCT_OWNER_CORREO = '46'
ID_INSIGHT_OBJECT_PRODUCT_OWNER_TELEFONO = '45'
ID_INSIGHT_OBJECT_COMPONENTE_NEGOCIO = '4'
ID_INSIGHT_OBJECT_COMP_NEGOCIO_NOMBRE = '14'
ID_INSIGHT_OBJECT_COMP_NEGOCIO_PRODUCTO = '42'
ID_INSIGHT_OBJECT_COMP_NEGOCIO_SID = '50'
ID_INSIGHT_OBJECT_DATOS_PERSONALES = '103'
ID_INSIGHT_OBJECT_DATOS_PROTEGIDOS = '104'
ID_INSIGHT_OBJECT_DATOS_CONFIDENCIALES = '105'
ID_BOARD_KANBAN = 255

sh = SecretHelper()
JIRA_USER = sh.get_secret("USER_JIRA", True)
JIRA_PW = sh.get_secret("PSWD_JIRA", True)
HOST = URL
CONFLUENCE_USER = sh.get_secret("USER_CONFLUENCE", True) # Secretos cifrados en SM.
CONFLUENCE_PW = sh.get_secret("PSWD_CONFLUENCE", True)
HOST_CONFLUENCE = HOST_CONFLUENCE


def lambda_handler(event, context):
    # ------CATEGORIAS--------
    # Recojo las categorias y formo el par ID--Nombre
    categorias = get_project_category()
    print(categorias)
    categorias_options = ""
    negocio_nombre = ""
    for j in range(len(categorias)):
        categorias_options += str(categorias[j]
                                  ['id'])+'-'+categorias[j]['name']+'\n'

    # ------INPUT--------
    errores = {}
    nombre_prod = event.get("nombre_prod")
    if not nombre_prod:
        errores["nombre_prod"] = "ERROR: Introduzca el valor de nombre_prod"

    key_prod = event.get("key_prod")
    if not key_prod or len(key_prod) < 2 or len(key_prod) > 10:
        errores["key_prod"] = "ERROR: La clave del producto debe tener entre "\
            "2 y 10 caracteres"

    negocio = event.get("negocio")
    if not negocio or len(negocio) != 5 or not negocio.isdigit():
        errores["negocio"] = "El formato del Negocio introducido no " \
            "es correcto.Introduzca un ID valido"
    else:
        encontrado = False
        i = 0
        while not encontrado and i < len(categorias):
            if categorias[i]['id'] == negocio:
                encontrado = True
                negocio_nombre = categorias[i]['name']
            i = i+1
        if not encontrado:
            errores["negocio"] = "El ID del Negocio no existe. " \
                "Introduzca un ID valido."

    if errores:
        return json.dumps(errores)
    # ------PROYECTO--------
    project_attributes = create_project(
        nombre_prod, key_prod, negocio, '1')

    # -------GRUPOS---------
    grupo_dev = create_groups(nombre_prod, 'developers')
    grupo_scrum = create_groups(nombre_prod, 'scrumMasters')
    grupo_auditors = create_groups(nombre_prod, 'auditors')
    grupo_admin = create_groups(nombre_prod, 'admins')
    grupo_agents = create_groups(nombre_prod, 'agents')
    grupo_editors = create_groups(nombre_prod, 'editors')

    add_admin_groups(grupo_dev)
    add_admin_groups(grupo_scrum)
    add_admin_groups(grupo_auditors)
    add_admin_groups(grupo_admin)
    add_admin_groups(grupo_editors)

    asignar_rol(grupo_admin, str(project_attributes['pid']), IDROL_ADMIN)
    asignar_rol(grupo_dev, str(project_attributes['pid']), IDROL_DEV)
    asignar_rol(grupo_scrum, str(project_attributes['pid']), IDROL_SCRUM)
    asignar_rol(grupo_auditors, str(
        project_attributes['pid']), IDROL_AUDITOR)
    asignar_rol('observadores', str(
        project_attributes['pid']), IDROL_AUDITOR)
    # ------ASIGNO EL GRUPO admin AL ROL SERVICE DESK TEAM DEL HELP DESK
    asignar_rol(grupo_agents, ID_SERVICE_DESK_PROJECT,
                IDROL_SERVICEDESKTEAM)
    # -----ASIGNO LOS GRUPOS AL ROL AUDITORS DE SVD
    asignar_rol(grupo_admin, ID_SERVICE_DESK_PROJECT, IDROL_AUDITOR)
    asignar_rol(grupo_dev, ID_SERVICE_DESK_PROJECT, IDROL_AUDITOR)
    asignar_rol(grupo_scrum, ID_SERVICE_DESK_PROJECT, IDROL_AUDITOR)
    asignar_rol(grupo_auditors, ID_SERVICE_DESK_PROJECT, IDROL_AUDITOR)

    space_attributes = create_space(
        nombre_prod, key_prod)  # Creo el espacio

    homepage_new_space = space_attributes['homepage']['id']
    content = get_page(ID_TEMPLATE_HOME)

    bod_template_home = content['body']['storage']['value']
    if bod_template_home.find("project="+ESPACIO_PLANTILLA) != -1:
        bod_template_home = bod_template_home.replace(
            "project="+ESPACIO_PLANTILLA, "project="+key_prod)

    print("homepageNewSpace:"+homepage_new_space)
    result = update_page_content(
        homepage_new_space, bod_template_home, nombre_prod)

    hijas = get_child_page(ID_TEMPLATE_HOME, ESPACIO_PLANTILLA)['results']

    for hija in hijas:
        id_hija = hija['id']
        titulo = hija['title']
        body = hija['body']['storage']['value']
        if body.find(ESPACIO_PLANTILLA) != -1:
            body = body.replace(ESPACIO_PLANTILLA, key_prod)
        pagina_nueva = create_content(
            key_prod, titulo, body, homepage_new_space)
        crearHijas(key_prod, ESPACIO_PLANTILLA, id_hija, pagina_nueva['id'])

    return 'Se ha creado correctamente el Producto en Jira y confluence_pw'


def get_project_category():
    url = HOST+'/rest/api/2/projectCategory'
    try:
        req = requests.get(url, auth=(JIRA_USER, JIRA_PW), verify=True)
        if not req.status_code in range(200, 206):
            print(req.status_code)
            print('Error connecting to Jira.. check config file')
            sys.exit
        jira = req.json()
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))


def create_project(nombre_prod, key, projectCategory, id_template):
    url = HOST+'/rest/projecttemplates/1.0/create-templates/create'

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    json = 'projectKey='+key+'&projectName='+nombre_prod+'&templateId=' + \
        id_template+'&projectCategoryId='+projectCategory+'&projectLead='
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(JIRA_USER, JIRA_PW),
                            data=json, headers=headers, verify=False)
        # check return
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira.. check config file')
            sys.exit()
        jira = req.json()
        print("Creado proyecto:"+nombre_prod)
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error creating new Jira project')


def create_groups(nombre_prod, rol):
    url = HOST+'/rest/api/2/group'
    headers = {'Content-Type': 'application/json'}
    nombre_prod = nombre_prod.lower()
    json = '{"name":\"'+nombre_prod+'_'+rol+'\"}'
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(JIRA_USER, JIRA_PW),
                            data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira... check config file')
            sys.exit()
        jira = req.json()
        print("Grupo creado:"+nombre_prod+'_'+rol)
        return nombre_prod+'_'+rol
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error creating new Jira groups')


def add_admin_groups(group):
    url = HOST+'/rest/api/2/group/user?groupname='+group
    headers = {'Content-Type': 'application/json'}
    json = '{"name":\"'+JIRA_USER+'\"}'
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(JIRA_USER, JIRA_PW),
                            data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira... check config file')
            sys.exit()
        jira = req.json()
        print("Admin anadido a:"+group)
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error adding admin to group')


def get_child_page(idparentpage, key):
    url = HOST_CONFLUENCE+'/wiki/rest/api/content/' + \
        str(idparentpage)+'/child?expand=page'
    try:
        req = requests.get(url, auth=(
            CONFLUENCE_USER, CONFLUENCE_PW), verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Confluence.. check config file')
            sys.exit
        jira = req.json()
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to Confluence')
    except requests.exceptions.RequestException as exep:
        print('error connecting to Confluence: ' + str(exep))


def asignar_rol(group, project_id, rol_id):
    url = HOST+'/rest/api/2/project/'+project_id+'/role/'+rol_id
    headers = {'Content-Type': 'application/json'}
    if 'admin' in group:
        json = '{"group":["'+group+'"]}'
    else:
        json = '{"group":["'+group+'"]}'
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(JIRA_USER, JIRA_PW),
                            data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira... check config file')
            sys.exit()
        jira = req.json()
        print('Asignado '+group+' al rol correspondiente')
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error assigning group '+group)


def create_filter(nombre_prod, clave_prod, insightKey):
    url = HOST+'/rest/api/2/filter'
    headers = {'Content-Type': 'application/json'}
    jql = 'project in ('+clave_prod+',SVD) AND \\"Producto Afectado\\" =\\"' + \
        insightKey+'\\" ORDER BY rank'
    nombre = nombre_prod+'_Filtro'
    json = '{"name":"'+nombre+'","jql":"'+jql+'","favourite":true}'
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(JIRA_USER, JIRA_PW),
                            data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira... check config file')
            sys.exit()
        jira = req.json()
        print("Filtro creado "+nombre)
        return jira['id']
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error creating filter')


def filter_permissions(filter_id, group):
    url = HOST+'/rest/api/2/filter/'+filter_id+'/permission'
    headers = {'Content-Type': 'application/json'}
    json = '{"type":"group","groupname":"'+group+'"}'
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(JIRA_USER, JIRA_PW),
                            data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira... check config file')
            sys.exit()
        jira = req.json()
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error changing filter permissions ')


def create_board(filter_id, clave_prod, nombre_prod):
    url = HOST+'/rest/agile/1.0/board'
    headers = {'Content-Type': 'application/json'}
    json = '{"filterId":'+filter_id+',"name":"Help Desk Zone ' + \
        nombre_prod+'","type":"kanban"}'
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(JIRA_USER, JIRA_PW),
                            data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira... check config file')
            sys.exit()
        jira = req.json()
        print("kanban board creado")
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error creating scrum board ')


def copy_board(idBoard):
    url = HOST+'/rest/greenhopper/1.0/rapidview/'+str(idBoard)+'/copy'
    try:
        req = requests.put(url, auth=(JIRA_USER, JIRA_PW), verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira.. check config file ' +
                  str(req.status_code))
            sys.exit
        jira = req.json()
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to Jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to Jira: ' + str(exep))


def change_filter(idBoard, idFilter):
    url = HOST+'/rest/greenhopper/1.0/rapidviewconfig/filter'
    headers = {'Content-Type': 'application/json'}
    json = '{"id":'+str(idBoard)+',"savedFilterId":"'+str(idFilter)+'"}'
    json = json.encode("UTF8")
    try:
        req = requests.put(url, auth=(JIRA_USER, JIRA_PW),
                           data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira.. check config file ' +
                  str(req.status_code))
            sys.exit
        jira = req.json()
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to Jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to Jira: ' + str(exep))


def change_name(idBoard, nombre):
    url = HOST+'/rest/greenhopper/1.0/rapidviewconfig/name'
    headers = {'Content-Type': 'application/json'}
    json = '{"id":'+str(idBoard)+',"name":"Help Desk Zone '+nombre+'"}'
    json = json.encode("UTF8")
    try:
        req = requests.put(url, auth=(JIRA_USER, JIRA_PW),
                           data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira.. check config file ' +
                  str(req.status_code))
            sys.exit
        jira = req.json()
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to Jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to Jira: ' + str(exep))


def create_negocio_insight(name):
    url = HOST+'/rest/insight/1.0/object/create'
    headers = {'Content-Type': 'application/json'}

    json = '{"objectTypeId":'+ID_INSIGHT_OBJECT_NEGOCIO + \
        ',"attributes":[{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_NEGOCIO_NAME + \
        ',"objectAttributeValues":[{"value":"'+name+'"}]}]}'
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(JIRA_USER, JIRA_PW),
                            data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira... check config file')
            sys.exit()
        jira = req.json()
        print("Objeto Insight Negocio creado")
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error creating insight object Negocio')


def check_negocio_insight(nombreNegocio):
    url = HOST+'/rest/insight/1.0/objecttype/3/objects'
    headers = {'Content-Type': 'application/json'}
    try:
        req = requests.get(url, auth=(JIRA_USER, JIRA_PW), verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira... check config file')
            sys.exit()
        insight = req.json()
        i = 0
        encontrado = False
        while(encontrado == False and i < len(insight)):
            if(insight[i].get('label') == nombreNegocio):
                return insight[i].get('objectKey')
                encontrado = True
            i = i+1
        if encontrado == False:
            nuevoNegocio = create_negocio_insight(nombreNegocio)
            return nuevoNegocio['objectKey']
        else:
            print("NEGOCIO " + nombreNegocio + " ENCONTRADO")
        return insight
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error creating insight object ')


def create_insight(name, claveNegocio, PO, POtelef, POemail, respNegocio,
                   respNegocioCorreo, respNegocioTelef, respOperacion,
                   respOperacionCorreo, respOperacionTelef, respDesarrollo,
                   respDesarrolloCorreo, respDesarrolloTelef, datosPersonales,
                   datosProtegidos, datosConfidenciales):
    url = HOST+'/rest/insight/1.0/object/create'
    headers = {'Content-Type': 'application/json'}
    json_respNegocio = '{"objectTypeAttributeId":'+idInsightObjectRespNegocio \
        + ',"objectAttributeValues":[{"value":"'+respNegocio + \
        '"}]},{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_RESP_NEGOCIO_CORREO + \
        ',"objectAttributeValues":[{"value":"'+respNegocioCorreo + \
        '"}]},{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_RESP_NEGOCIO_TELEFONO + \
        ',"objectAttributeValues":[{"value":"'+respNegocioTelef+'"}]}'
    json_respOperacion = '{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_RESP_OPERACION + \
        ',"objectAttributeValues":[{"value":"'+respOperacion + \
        '"}]},{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_RESP_OPERACION_CORREO + \
        ',"objectAttributeValues":[{"value":"'+respOperacionCorreo + \
        '"}]},{"objectTypeAttributeId":' + \
        idInsightObjectRespOperacionTelefono + \
        ',"objectAttributeValues":[{"value":"'+respOperacionTelef+'"}]}'
    json_respDesarrollo = '{"objectTypeAttributeId":' + \
        idInsightObjectRespDesarrollo + \
        ',"objectAttributeValues":[{"value":"'+respDesarrollo + \
        '"}]},{"objectTypeAttributeId":'+idInsightObjectRespDesarrolloCorreo + \
        ',"objectAttributeValues":[{"value":"'+respDesarrolloCorreo + \
        '"}]},{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_RESP_DESARROLLO_TELEFONO + \
        ',"objectAttributeValues":[{"value":"'+respDesarrolloTelef+'"}]}'
    json_po = '{"objectTypeAttributeId":'+ID_INSIGHT_OBJECT_PRODUCT_OWNER + \
        ',"objectAttributeValues":[{"value":"'+PO + \
        '"}]},{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_PRODUCT_OWNER_CORREO + \
        ',"objectAttributeValues":[{"value":"'+POemail + \
        '"}]},{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_PRODUCT_OWNER_TELEFONO + \
        ',"objectAttributeValues":[{"value":"'+POtelef+'"}]}'
    json_datos = '{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_DATOS_PERSONALES + \
        ',"objectAttributeValues":[{"value":"'+datosPersonales + \
        '"}]},{"objectTypeAttributeId":'+ID_INSIGHT_OBJECT_DATOS_PROTEGIDOS + \
        ',"objectAttributeValues":[{"value":"'+datosProtegidos + \
        '"}]},{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_DATOS_CONFIDENCIALES + \
        ',"objectAttributeValues":[{"value":"'+datosConfidenciales+'"}]}'

    json = '{"objectTypeId":'+ID_INSIGHT_OBJECT + \
        ',"attributes":[{"objectTypeAttributeId":'+ID_INSIGHT_OBJECT_NAME + \
        ',"objectAttributeValues":[{"value":"'+name + \
        '"}]},{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_NEGOCIO_ATTRIBUTE + \
        ',"objectAttributeValues":[{"value":"'+claveNegocio+'"}]},' + \
        json_respNegocio+','+json_respOperacion+',' + \
        json_respDesarrollo+','+json_po+','+json_datos+']}'
    print(json)
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(JIRA_USER, JIRA_PW),
                            data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira... check config file')
            sys.exit()
        jira = req.json()
        print("Objeto Insight creado")
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error creating insight object ')


def create_componenteNegocio(name, claveProducto):
    url = HOST+'/rest/insight/1.0/object/create'
    headers = {'Content-Type': 'application/json'}

    json = '{"objectTypeId":'+ID_INSIGHT_OBJECT_COMPONENTE_NEGOCIO + \
        ',"attributes":[{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_COMP_NEGOCIO_NOMBRE + \
        ',"objectAttributeValues":[{"value":"'+name + \
        '"}]},{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_COMP_NEGOCIO_PRODUCTO + \
        ',"objectAttributeValues":[{"value":"'+claveProducto + \
        '"}]},{"objectTypeAttributeId":' + \
        ID_INSIGHT_OBJECT_COMP_NEGOCIO_SID + \
        ',"objectAttributeValues":[{"value":true}]}]}'
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(JIRA_USER, JIRA_PW),
                            data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira... check config file')
            sys.exit()
        jira = req.json()
        print("Objeto Insight creado")
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error creating insight object ')


def search_key():
    url = HOST + '/rest/api/2/project'
    try:
        req = requests.get(url, auth=(JIRA_USER, JIRA_PW), verify=False)

        if not req.status_code in range(200, 206):
            print('Error connecting to Jira.. check config file')
            sys.exit()
        jira = req.json()
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        # catastrophic error. bail.
        print('error connecting to jira: ' + str(exep))


def create_space(name, key):
    url = HOST_CONFLUENCE+'/rest/api/space'
    headers = {'Content-Type': 'application/json'}

    json = '{"key":"'+key+'","name":"'+name+'"}'
    json = json.encode("UTF8")
    print(json)
    try:
        req = requests.post(url, auth=(CONFLUENCE_USER, CONFLUENCE_PW),
                            data=json, headers=headers, verify=False)
        # check return
        if not req.status_code in range(200, 206):
            print('Error connecting to Confluence.. check config file')
            sys.exit()
        jira = req.json()
        print("Creado espacio:"+name)
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to Confluence')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error creating new Confluence space')


def create_content(key, title, page_json, parentID):
    url = HOST_CONFLUENCE+'/rest/api/content'
    page_json = page_json.replace('"', '\\"')
    page_json = page_json.replace('\n', '\\n')
    headers = {'Content-Type': 'application/json'}
    json = '{"type":"page","title":"'+title+'","space":{"key":"'+key + \
        '"},"ancestors": [{"id":'+str(parentID) + \
        '}],"status":"current","body": {"storage":{"value":"'+page_json + \
        '","representation":"storage"}}}'
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(CONFLUENCE_USER, CONFLUENCE_PW),
                            data=json, headers=headers, verify=False)
        # check return
        if not req.status_code in range(200, 206):
            print('Error connecting to Confluence.. check config file')
            sys.exit()
        jira = req.json()
        print("Creada pagina:"+title)
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to Confluence')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error creating new Confluence page:'+title)


def get_page(idPage):
    url = HOST_CONFLUENCE+'/rest/api/content/' + \
        idPage+'?expand=body.storage,ancestors'
    try:
        req = requests.get(url, auth=(
            CONFLUENCE_USER, CONFLUENCE_PW), verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Confluence.. check config file')
            sys.exit
        jira = req.json()
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to Confluence')
    except requests.exceptions.RequestException as exep:
        print('error connecting to Confluence: ' + str(exep))


def update_page_content(homepageID, body, title):
    body = body.replace('"', '\\"')
    body = body.replace('\n', '\\n')
    url = HOST_CONFLUENCE+'/rest/api/content/'+str(homepageID)
    headers = {'Content-Type': 'application/json'}
    json = '{"version":{"number":2},"type":"page","title":"'+title + \
        '","body":{"storage":{"value":"'+body+'","representation":"storage"}}}'
    json = json.encode("UTF8")
    try:
        req = requests.put(url, auth=(CONFLUENCE_USER, CONFLUENCE_PW),
                           data=json, headers=headers, verify=False)
        # check return
        if not req.status_code in range(200, 206):
            print('Error connecting to Confluence.. check config file')
            sys.exit()
        jira = req.json()
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to Confluence')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error updating space main page')


def create_group_confluence(name, rol):
    url = HOST_CONFLUENCE+'/rest/api/3/group'
    headers = {'Content-Type': 'application/json'}
    name = name.lower()
    json = '{"name":\"'+name+'_'+rol+'\"}'
    json = json.encode("UTF8")
    try:
        req = requests.post(url, auth=(CONFLUENCE_USER, CONFLUENCE_PW),
                            data=json, headers=headers, verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Jira... check config file')
            sys.exit()
        jira = req.json()
        print("Grupo "+name+" creado")
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to jira')
    except requests.exceptions.RequestException as exep:
        print('error connecting to jira: ' + str(exep))
    except:
        print('error creating group '+name+'_'+rol)


def get_child_page(idparentpage, key):
    url = HOST_CONFLUENCE + \
        '/rest/api/content/search?cql=(parent='+str(idparentpage) + \
        ')&expand=body.storage&limit=1000'
    try:
        req = requests.get(url, auth=(
            CONFLUENCE_USER, CONFLUENCE_PW), verify=False)
        if not req.status_code in range(200, 206):
            print('Error connecting to Confluence.. check config file')
            sys.exit
        jira = req.json()
        return jira
    except requests.exceptions.Timeout:
        print('Timeout trying to connect to Confluence')
    except requests.exceptions.RequestException as exep:
        print('error connecting to Confluence: ' + str(exep))


def crearHijas(key_prod, espacioPlantilla,
               idPaginaPlantilla, idPaginaNewSpace):
    pageCheck = get_child_page(idPaginaPlantilla, espacioPlantilla)['results']
    if len(pageCheck) > 0:
        for p in pageCheck:
            idPage = p['id']
            titulo = p['title']
            body = p['body']['storage']['value']
            if body.find(espacioPlantilla) != -1:
                body = body.replace(espacioPlantilla, key_prod)
            nuevaPage = create_content(
                key_prod, titulo, body, idPaginaNewSpace)
            crearHijas(key_prod, espacioPlantilla, idPage, nuevaPage['id'])
