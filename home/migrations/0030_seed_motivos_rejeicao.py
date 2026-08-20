from django.db import migrations


def seed_motivos(apps, schema_editor):
    MotivoRejeicao = apps.get_model("home", "MotivoRejeicao")
    padroes = [
        (0, "Já tocámos esta música"),
        (1, "Não temos o repertório"),
        (2, "Fora do estilo da roda"),
        (3, "Fila muito longa / sem tempo"),
        (4, "Pedido incompleto ou inválido"),
        (5, "Outro"),
    ]
    for ordem, nome in padroes:
        MotivoRejeicao.objects.get_or_create(
            nome=nome,
            defaults={"ordem": ordem, "ativo": True},
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0029_motivo_rejeicao"),
    ]

    operations = [
        migrations.RunPython(seed_motivos, noop_reverse),
    ]
