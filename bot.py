import os
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands

# =========================================================
# CONFIGURAÇÃO
# =========================================================

TOKEN = os.getenv("MTU2MDQwNTc0ODA5NjMwMzIzNw.GQuWCT.9TDHTPnPBMtB1VsWqi2hTL9brDdQTeFDCPbQnM")

if not TOKEN:
    raise RuntimeError(
        "A variável DISCORD_TOKEN não foi configurada."
    )

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

DB = "detran_advertencias.db"

# =========================================================
# BANCO DE DADOS
# =========================================================

def iniciar_banco():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advertencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agente_id TEXT NOT NULL,
            mencao TEXT NOT NULL,
            nome TEXT NOT NULL,
            motivo TEXT NOT NULL,
            gravidade TEXT NOT NULL,
            penalidade TEXT NOT NULL,
            fim_suspensao TEXT NOT NULL,
            justificativa TEXT NOT NULL,
            aplicador TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def salvar_adv(dados):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO advertencias
        (
            agente_id,
            mencao,
            nome,
            motivo,
            gravidade,
            penalidade,
            fim_suspensao,
            justificativa,
            aplicador,
            data
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, dados)

    conn.commit()
    conn.close()


# =========================================================
# CANAL DE LOG
# =========================================================

async def pegar_canal_logs(guild):

    canal = discord.utils.get(
        guild.text_channels,
        name="📋・logs-advertencias"
    )

    if canal:
        return canal

    try:
        canal = await guild.create_text_channel(
            "📋・logs-advertencias"
        )
        return canal

    except discord.Forbidden:
        return None


# =========================================================
# EMBED DA ADVERTÊNCIA
# =========================================================

def criar_embed(d):

    embed = discord.Embed(
        title="⚠️ REGISTRO DE ADVERTÊNCIA (ADV)",
        description="🚔 **DETRAN-DF | MTA**",
        color=discord.Color.red()
    )

    embed.add_field(
        name="👤 ID do agente",
        value=f"`{d['agente_id']}`  {d['mencao']}",
        inline=False
    )

    embed.add_field(
        name="🎮 Nome do agente",
        value=d["nome"],
        inline=False
    )

    embed.add_field(
        name="📋 MOTIVO",
        value=d["motivo"],
        inline=False
    )

    embed.add_field(
        name="🔴 GRAVIDADE",
        value=d["gravidade"],
        inline=False
    )

    embed.add_field(
        name="⚖️ PENALIDADE ADMINISTRATIVA",
        value=(
            f"{d['penalidade']}\n"
            f"**FIM DA SUSPENSÃO:** {d['fim_suspensao']}"
        ),
        inline=False
    )

    embed.add_field(
        name="📑 JUSTIFICATIVA",
        value=d["justificativa"],
        inline=False
    )

    embed.add_field(
        name="📢 DETERMINAÇÃO",
        value=(
            "O agente fica formalmente advertido e deverá cumprir "
            "integralmente a penalidade aplicada.\n\n"
            "Reforça-se que todos os integrantes do DETRAN-DF "
            "devem conhecer e respeitar as regras do servidor, "
            "mantendo uma conduta compatível com suas responsabilidades.\n\n"
            "A reincidência poderá resultar em medidas disciplinares "
            "mais severas, conforme as normas vigentes."
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ APLICADOR DA ADV",
        value=d["aplicador"],
        inline=False
    )

    embed.set_footer(
        text="🚔 DETRAN-DF — Disciplina, responsabilidade e compromisso com as regras."
    )

    return embed


# =========================================================
# FORMULÁRIO
# =========================================================

class AdvModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(
            title="⚠️ Registrar Advertência - DETRAN-DF"
        )

    agente_id = discord.ui.TextInput(
        label="ID do agente",
        placeholder="Ex.: 25709",
        max_length=20
    )

    mencao = discord.ui.TextInput(
        label="Menção do Discord",
        placeholder="Ex.: <@1515838172167147720>",
        max_length=100
    )

    nome = discord.ui.TextInput(
        label="Nome do agente",
        placeholder="Ex.: kmdia_midia",
        max_length=100
    )

    motivo = discord.ui.TextInput(
        label="Motivo da ADV",
        placeholder="Digite o motivo da advertência.",
        style=discord.TextStyle.paragraph,
        max_length=1000
    )

    penalidade = discord.ui.TextInput(
        label="Penalidade administrativa",
        placeholder="Ex.: Suspensão dos direitos de agente por 02 dias.",
        style=discord.TextStyle.paragraph,
        max_length=1500
    )

    async def on_submit(self, interaction):

        dados = {
            "agente_id": str(self.agente_id),
            "mencao": str(self.mencao),
            "nome": str(self.nome),
            "motivo": str(self.motivo),
            "penalidade": str(self.penalidade),
            "aplicador": interaction.user.mention
        }

        await interaction.response.send_message(
            "📅 Agora informe a **data do fim da suspensão** e escolha a gravidade:",
            view=GravidadeView(dados),
            ephemeral=True
        )


# =========================================================
# GRAVIDADE
# =========================================================

class GravidadeView(discord.ui.View):

    def __init__(self, dados):
        super().__init__(timeout=300)
        self.dados = dados

    async def finalizar(
        self,
        interaction,
        gravidade
    ):

        self.dados["gravidade"] = gravidade

        await interaction.response.send_modal(
            DataFinalModal(self.dados)
        )

    @discord.ui.button(
        label="Baixa",
        emoji="🟢",
        style=discord.ButtonStyle.success
    )
    async def baixa(self, interaction, button):

        await self.finalizar(
            interaction,
            "Baixa"
        )

    @discord.ui.button(
        label="Média",
        emoji="🟠",
        style=discord.ButtonStyle.primary
    )
    async def media(self, interaction, button):

        await self.finalizar(
            interaction,
            "Média"
        )

    @discord.ui.button(
        label="Grave",
        emoji="🔴",
        style=discord.ButtonStyle.danger
    )
    async def grave(self, interaction, button):

        await self.finalizar(
            interaction,
            "Grave"
        )


# =========================================================
# DATA FINAL
# =========================================================

class DataFinalModal(discord.ui.Modal):

    def __init__(self, dados):
        super().__init__(
            title="📅 Finalização da Advertência"
        )

        self.dados = dados

    fim_suspensao = discord.ui.TextInput(
        label="Fim da suspensão",
        placeholder="Ex.: 18/10/26",
        max_length=30
    )

    justificativa = discord.ui.TextInput(
        label="Justificativa",
        placeholder="Explique o motivo da punição.",
        style=discord.TextStyle.paragraph,
        max_length=2000
    )

    async def on_submit(self, interaction):

        self.dados["fim_suspensao"] = str(
            self.fim_suspensao
        )

        self.dados["justificativa"] = str(
            self.justificativa
        )

        salvar_adv((
            self.dados["agente_id"],
            self.dados["mencao"],
            self.dados["nome"],
            self.dados["motivo"],
            self.dados["gravidade"],
            self.dados["penalidade"],
            self.dados["fim_suspensao"],
            self.dados["justificativa"],
            self.dados["aplicador"],
            discord.utils.utcnow().strftime(
                "%d/%m/%Y %H:%M"
            )
        ))

        embed = criar_embed(self.dados)

        canal = await pegar_canal_logs(
            interaction.guild
        )

        if canal:
            await canal.send(
                embed=embed
            )

        await interaction.response.send_message(
            "✅ **ADV registrada com sucesso!**\n"
            "📋 O registro foi enviado para o canal de logs.",
            ephemeral=True
        )


# =========================================================
# HISTÓRICO
# =========================================================

async def mostrar_historico(interaction):

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            agente_id,
            nome,
            gravidade,
            motivo,
            data
        FROM advertencias
        ORDER BY id DESC
        LIMIT 10
    """)

    registros = cursor.fetchall()

    conn.close()

    if not registros:

        await interaction.response.send_message(
            "📋 **Nenhuma advertência registrada.**",
            ephemeral=True
        )

        return

    texto = ""

    for registro in registros:

        texto += (
            f"👤 **ID:** `{registro[0]}`\n"
            f"🎮 **Agente:** {registro[1]}\n"
            f"🔴 **Gravidade:** {registro[2]}\n"
            f"📋 **Motivo:** {registro[3]}\n"
            f"📅 **Data:** {registro[4]}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
        )

    embed = discord.Embed(
        title="📋 HISTÓRICO DE ADVERTÊNCIAS",
        description=texto,
        color=discord.Color.orange()
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# =========================================================
# PAINEL
# =========================================================

class PainelAdv(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Registrar ADV",
        emoji="⚠️",
        style=discord.ButtonStyle.danger,
        custom_id="detran_registrar_adv"
    )
    async def registrar(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            AdvModal()
        )

    @discord.ui.button(
        label="Histórico",
        emoji="📋",
        style=discord.ButtonStyle.secondary,
        custom_id="detran_historico_adv"
    )
    async def historico(
        self,
        interaction,
        button
    ):

        await mostrar_historico(
            interaction
        )


# =========================================================
# COMANDO /PAINEL-ADV
# =========================================================

@bot.tree.command(
    name="painel-adv",
    description="Abrir o painel de advertências do DETRAN-DF."
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def painel_adv(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="⚠️ SISTEMA DE ADVERTÊNCIAS — DETRAN-DF",
        description=(
            "Utilize os botões abaixo para registrar e "
            "consultar advertências disciplinares."
        ),
        color=discord.Color.red()
    )

    embed.add_field(
        name="⚠️ REGISTRAR ADV",
        value=(
            "Clique para registrar uma nova advertência."
        ),
        inline=False
    )

    embed.add_field(
        name="📋 HISTÓRICO",
        value=(
            "Consulte as últimas advertências registradas."
        ),
        inline=False
    )

    embed.set_footer(
        text="DETRAN-DF | Sistema Disciplinar"
    )

    await interaction.response.send_message(
        embed=embed,
        view=PainelAdv()
    )


# =========================================================
# COMANDO !PAINEL
# =========================================================

@bot.command()
@commands.has_permissions(
    manage_guild=True
)
async def painel(ctx):

    embed = discord.Embed(
        title="⚠️ SISTEMA DE ADVERTÊNCIAS — DETRAN-DF",
        description=(
            "Clique em **Registrar ADV** para abrir "
            "o formulário de advertência."
        ),
        color=discord.Color.red()
    )

    await ctx.send(
        embed=embed,
        view=PainelAdv()
    )


# =========================================================
# INICIALIZAÇÃO
# =========================================================

@bot.event
async def on_ready():

    iniciar_banco()

    # Mantém os botões funcionando após reiniciar.
    bot.add_view(
        PainelAdv()
    )

    try:

        await bot.tree.sync()

    except Exception as erro:

        print(
            f"Erro ao sincronizar comandos: {erro}"
        )

    print(
        f"✅ Bot conectado como {bot.user}"
    )

    print(
        "🚔 Sistema DETRAN-DF iniciado!"
    )


# =========================================================
# INICIAR BOT
# =========================================================

bot.run(TOKEN)