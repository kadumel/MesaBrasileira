from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0035_eventodestaque_midias_url"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sobrepagina",
            name="subtitulo",
        ),
        migrations.RenameField(
            model_name="sobrepagina",
            old_name="texto_samba_na_rua",
            new_name="texto_quem_somos",
        ),
        migrations.RenameField(
            model_name="sobrepagina",
            old_name="texto_nossa_essencia",
            new_name="texto_roda_por_todos",
        ),
        migrations.RenameField(
            model_name="sobrepagina",
            old_name="texto_ponto_encontro",
            new_name="texto_respeito_samba",
        ),
        migrations.RenameField(
            model_name="sobrepagina",
            old_name="texto_mais_que_musica",
            new_name="texto_cultura_primeiro",
        ),
        migrations.AlterField(
            model_name="sobrepagina",
            name="texto_quem_somos",
            field=models.TextField(
                blank=True,
                help_text="Texto desta secção. Deixe linha em branco entre parágrafos.",
                verbose_name="Quem Somos",
            ),
        ),
        migrations.AlterField(
            model_name="sobrepagina",
            name="texto_roda_por_todos",
            field=models.TextField(
                blank=True,
                help_text="Texto desta secção. Deixe linha em branco entre parágrafos.",
                verbose_name="Uma roda feita por todos",
            ),
        ),
        migrations.AlterField(
            model_name="sobrepagina",
            name="texto_respeito_samba",
            field=models.TextField(
                blank=True,
                help_text="Texto desta secção. Deixe linha em branco entre parágrafos.",
                verbose_name="Em respeito ao nosso samba",
            ),
        ),
        migrations.AlterField(
            model_name="sobrepagina",
            name="texto_cultura_primeiro",
            field=models.TextField(
                blank=True,
                help_text="Texto desta secção. Deixe linha em branco entre parágrafos.",
                verbose_name="Cultura em primeiro lugar",
            ),
        ),
    ]
