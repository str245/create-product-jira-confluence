# Create Product Insight

This module deploys the infrastructure to manage create-product-jira-confluence Lambda.

## Infrastructure

The process use a servesless lambda to create:

- Project in Jira.

- Agile board.

- Filter.

- User groups.

- Project in Confluence.

- Groups permissions.

## Creating Spaces for a new Product

To create Jira and Confluence spaces just launch lambda with this parameters:
- negocio: Requerido. Código de la categoría de negocio de Jira para el producto. (Se puede consultar en "/rest/api/2/projectCategory")
- nombre_prod: Requerido. Nombre del Producto
- key_prod: Requerido. Clave del Producto

## Example usage

```json
{
  "nombre_prod": "Area Privada Seguridad",
  "key_prod": "SECpriv",
  "negocio": "1234"
}
```

## Deploying steps

To deploy the last changes done in this lambda to AWS follow this steps:

1. Create a zip file containing python scripts:

- LINUX. Simply execute *zipper.<span></span>sh* script
- WINDOWS. Manually, create the file **create-product-jira-confluence.zip** containing every python file present in **lambdas/create-product-jira-confluence** folder. Save this file inside this folder. (*Important: Name and path of zip file have to be the exactly the same as indicated before*)

2. Execute terraform commands as usually:

```bash
$ terraform init
$ terraform apply -var-file create-product-jira-confluence.tfvars
```
