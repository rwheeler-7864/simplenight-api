COMPUTE_URL_BASE = "https://www.googleapis.com/compute/v1/"


# noinspection PyUnusedLocal
def GenerateConfig(context):
    """Creates the second virtual machine."""

    deployment_name = "simplenight-api"
    instance_name = f"{deployment_name}-instance"
    database_name = f"{deployment_name}-db"
    region = "us-east1"
    tier = "db-custom-1-3840"

    resources = [
        {
            "name": instance_name,
            "type": "gcp-types/sqladmin-v1beta4:instances",
            "properties": {
                "region": region,
                "backendType": "SECOND_GEN",
                "databaseVersion": "POSTGRES_12",
                "settings": {"tier": tier, "backupConfiguration": {"enabled": True}},
            },
        },
        {
            "name": database_name,
            "type": "gcp-types/sqladmin-v1beta4:databases",
            "properties": {"name": database_name, "instance": f"$(ref.{instance_name}.name)", "charset": "utf8"},
        },
    ]

    return {"resources": resources}
