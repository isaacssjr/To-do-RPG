#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
To-Do App com XP System e Gamificação - VERSÃO 6.0
Desenvolvido para Isaac - Integra
Sistema de items, gold, streaks, badges, troféus mensais
Com ativação de itens permanentes, drops BALANCEADOS, LOJA com markup 5x
MODIFICAÇÕES V6.0:
- Botão de configurações com reset manual (reseta gold também)
- Campo de hora preenchido automaticamente com hora atual
- Novos valores de XP: low=3, medium=5, high=7
- Itens rebalanceados: livro (+2 XP, +1 Gold), espada (+1 XP, +2 Gold), escudo (+2 proteção)
- Sistema de Game: Baú diário e Expedição
"""

from __future__ import annotations

import sys
import os
import platform
import subprocess
import json
import webbrowser
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import List, Optional

# ============================================================
# SISTEMA DE INSTALAÇÃO ROBUSTO
# ============================================================

class DependencyManager:
    """Gerencia instalação de dependências de forma robusta"""

    def __init__(self):
        self.os_type = platform.system()
        self.python_version = sys.version_info
        self.installed = []
        self.failed = []

    def print_banner(self):
        """Exibe banner de inicialização"""
        print("""
╔════════════════════════════════════════════════════════════════╗
║  📝 TODO APP COM XP SYSTEM - VERSÃO 6.0                       ║
║  🚀 Isaac (Integra) - Sistema de Game Implementado            ║
║  ✨ Novidades: Reset Manual, Baú Diário, Expedição            ║
║  🔧 Verificando dependências...                               ║
╚════════════════════════════════════════════════════════════════╝
        """)
        print(f"🖥️  Sistema Operacional: {self.os_type}")
        print(f"🐍 Versão Python: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        print()

    def check_python_version(self) -> bool:
        """Verifica se Python é 3.8+"""
        if self.python_version.major < 3 or (self.python_version.major == 3 and self.python_version.minor < 8):
            print("❌ Erro: Python 3.8+ é obrigatório!")
            print(f"   Sua versão: {self.python_version.major}.{self.python_version.minor}")
            return False
        print("✅ Python versão compatível")
        return True

    def ensure_pip(self) -> bool:
        """Garante que pip está disponível"""
        try:
            import pip
            print("✅ pip já disponível")
            return True
        except ImportError:
            print("📦 Inicializando pip...")
            try:
                import ensurepip
                ensurepip.bootstrap()
                print("✅ pip inicializado com sucesso")
                return True
            except Exception as e:
                print(f"❌ Erro ao inicializar pip: {e}")
                return False

    def install_package(self, package: str, package_name: str = None) -> bool:
        """Instala pacote com verificações"""
        if package_name is None:
            package_name = package

        try:
            __import__(package_name)
            print(f"✅ {package} já instalado")
            self.installed.append(package)
            return True
        except ImportError:
            pass

        print(f"📥 Instalando {package}...", end=" ", flush=True)
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--quiet",
            package
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print("✅")
                self.installed.append(package)
                return True
            else:
                print("❌")
                self.failed.append(package)
                return False
        except subprocess.TimeoutExpired:
            print("⏱️ (timeout)")
            self.failed.append(package)
            return False
        except Exception as e:
            print(f"❌ ({str(e)[:50]})")
            self.failed.append(package)
            return False

    def install_all(self) -> bool:
        """Instala todas as dependências necessárias"""
        print("\n" + "="*60)
        print("📦 INSTALANDO DEPENDÊNCIAS")
        print("="*60 + "\n")

        dependencies = [("flask", "flask")]

        for package, import_name in dependencies:
            self.install_package(package, import_name)

        print("\n" + "="*60)
        print("📊 RESUMO DA INSTALAÇÃO")
        print("="*60)
        print(f"✅ Instalados: {len(self.installed)}")
        if self.failed:
            print(f"\n❌ Falharam: {len(self.failed)}")
            return False

        print("\n✅ Todas as dependências estão prontas!")
        return True

    def verify_imports(self) -> bool:
        """Verifica se todos os imports funcionam"""
        print("\n🔍 Verificando imports...", end=" ", flush=True)
        try:
            from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
            import webbrowser
            print("✅")
            return True
        except ImportError as e:
            print(f"❌\n   Erro: {e}")
            return False


# ============================================================
# ITENS E CONFIGURAÇÃO
# ============================================================

ITEMS_CONFIG = {
    "pizza": {
        "name": "Pizza Baratinha",
        "emoji": "🪳",
        "type": "consumable",
        "rarity": "common",
        "description": "Gasta 2 gold, ganha 2 XP",
        "cost": 2,
        "sell_price": 2,
        "shop_price": 10,
        "drop_chance": 0.15
    },
    "Cigarrinho": {
        "name": "Cigarrinho Mágico",
        "emoji": "🧃",
        "type": "consumable",
        "rarity": "common",
        "description": "Restaura XP perdido da última tarefa",
        "cost": 0,
        "sell_price": 5,
        "shop_price": 25,
        "drop_chance": 0.10
    },
    "cafe": {
        "name": "Café expresso",
        "emoji": "☕",
        "type": "consumable",
        "rarity": "rare",
        "description": "Dobra XP da próxima tarefa",
        "cost": 0,
        "sell_price": 5,
        "shop_price": 25,
        "drop_chance": 0.15
    },
    "bolsa": {
        "name": "Bolsa Mística",
        "emoji": "👜",
        "type": "permanent",
        "rarity": "epic",
        "description": "+6 espaço no inventário",
        "cost": 0,
        "sell_price": 40,
        "shop_price": 200,
        "drop_chance": 0.03,
        "effect": "bolsa_effect"
    },
    "livro": {
        "name": "Livro dos chamados",
        "emoji": "📖",
        "type": "permanent",
        "rarity": "epic",
        "description": "+2 XP e +1 Gold por tarefa",
        "cost": 0,
        "sell_price": 30,
        "shop_price": 150,
        "drop_chance": 0.03,
        "effect": "livro_effect"
    },
    "espada": {
        "name": "Espada Integrada",
        "emoji": "⚔️",
        "type": "permanent",
        "rarity": "epic",
        "description": "+1 XP e +2 Gold por tarefa",
        "cost": 0,
        "sell_price": 20,
        "shop_price": 100,
        "drop_chance": 0.03,
        "effect": "espada_effect"
    },
    "escudo": {
        "name": "Escudo do foco",
        "emoji": "🛡️",
        "type": "permanent",
        "rarity": "epic",
        "description": "+2 proteção em XP perdido",
        "cost": 0,
        "sell_price": 20,
        "shop_price": 100,
        "drop_chance": 0.03,
        "effect": "escudo_effect"
    },
    "coroa": {
        "name": "Coroa Integra",
        "emoji": "👑",
        "type": "permanent",
        "rarity": "legendary",
        "description": "2x Gold, botão Prioridade",
        "cost": 0,
        "sell_price": 60,
        "shop_price": 300,
        "drop_chance": 0.005,
        "effect": "coroa_effect"
    },
}

# Ordem fixa para itens comuns alinhados na loja
ORDER_FIX = ["pizza", "Cigarrinho", "cafe", "bolsa", "livro", "espada", "escudo", "coroa"]


# ============================================================
# Modelos e Classes
# ============================================================

@dataclass
class Trophy:
    month: str
    level: int
    earned_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def get_trophy_emoji(self) -> str:
        if self.level >= 3:
            return "🥇"
        elif self.level >= 2:
            return "🥈"
        else:
            return "🥉"


@dataclass
class Item:
    id: str
    name: str
    emoji: str
    rarity: str
    item_type: str
    description: str
    sell_price: int = 0
    equipped: bool = False

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        # Garante compatibilidade com saves antigos sem o campo 'equipped'
        if 'equipped' not in data:
            data['equipped'] = False
        return cls(**data)


@dataclass
class Badge:
    id: str
    name: str
    description: str
    emoji: str
    earned_at: str

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


AVAILABLE_BADGES = {
    "first_task": {"name": "Primeira Vitória", "description": "Complete sua primeira tarefa", "emoji": "🎯"},
    "streak_3": {"name": "Consistente", "description": "3 dias consecutivos", "emoji": "🔥"},
    "streak_7": {"name": "Dedicado", "description": "7 dias consecutivos", "emoji": "⚡"},
    "streak_30": {"name": "Imparável", "description": "30 dias consecutivos", "emoji": "💪"},
    "perfect_10": {"name": "Perfeição", "description": "10 tarefas no prazo seguidas", "emoji": "✨"},
    "speed_demon": {"name": "Velocista", "description": "Complete 5 tarefas em 1 hora", "emoji": "🚀"},
    "night_owl": {"name": "Coruja Noturna", "description": "Complete tarefa após 22h", "emoji": "🦉"},
    "early_bird": {"name": "Madrugador", "description": "Complete tarefa antes das 6h", "emoji": "🌅"},
    "task_master": {"name": "Mestre das Tarefas", "description": "100 tarefas concluídas", "emoji": "👑"},
    "level_10": {"name": "Veterano", "description": "Alcance nível 10", "emoji": "🏆"},
}


@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    priority: str = "low"
    category: str = "pessoal"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    completed: bool = False
    completed_at: Optional[str] = None
    completed_level: int = 0
    xp_earned: int = 0
    gold_earned: int = 0
    on_time: bool = False
    is_priority: bool = False

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def is_overdue(self) -> bool:
        if not self.due_date or not self.due_time or self.completed:
            return False
        try:
            due_datetime = datetime.fromisoformat(f"{self.due_date}T{self.due_time}")
            return datetime.now() > due_datetime
        except:
            return False


@dataclass
class UserStats:
    name: str = "Isaac"
    xp: int = 0
    gold: int = 0
    current_month: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m"))
    level: int = 0
    current_streak: int = 0
    best_streak: int = 0
    total_completed: int = 0
    perfect_streak: int = 0
    last_completion_date: Optional[str] = None
    last_xp_lost: int = 0
    double_xp_active: bool = False
    inventory: List[Item] = field(default_factory=list)
    badges: List[Badge] = field(default_factory=list)
    trophies: List[Trophy] = field(default_factory=list)
    max_inventory: int = 6
    recent_completions: List[str] = field(default_factory=list)  # Para speed_demon badge
    # Sistema de Game
    daily_chest_claimed: str = None  # Data do último baú aberto
    expedition_active: bool = False
    expedition_start_time: Optional[str] = None

    def to_dict(self):
        data = asdict(self)
        data['inventory'] = [i.to_dict() for i in self.inventory]
        data['badges'] = [b.to_dict() for b in self.badges]
        data['trophies'] = [t.to_dict() for t in self.trophies]
        return data

    @classmethod
    def from_dict(cls, data):
        inventory = [Item.from_dict(i) for i in data.pop('inventory', [])]
        badges = [Badge.from_dict(b) for b in data.pop('badges', [])]
        trophies = [Trophy.from_dict(t) for t in data.pop('trophies', [])]
        max_inventory = data.pop('max_inventory', 6)
        daily_chest_claimed = data.pop('daily_chest_claimed', None)
        expedition_active = data.pop('expedition_active', False)
        expedition_start_time = data.pop('expedition_start_time', None)
        stats = cls(**data)
        stats.inventory = inventory
        stats.badges = badges
        stats.trophies = trophies
        stats.max_inventory = max_inventory
        stats.daily_chest_claimed = daily_chest_claimed
        stats.expedition_active = expedition_active
        stats.expedition_start_time = expedition_start_time
        return stats

    def get_xp_for_level(self):
        return self.xp % 100

    def get_xp_needed_for_level(self):
        return 100

    def get_progress_percent(self):
        return int((self.get_xp_for_level() / 100) * 100)

    def get_rank_title(self) -> str:
        if self.level >= 100: return "🌟 Lendário"
        elif self.level >= 75: return "💎 Diamante"
        elif self.level >= 50: return "👑 Mestre"
        elif self.level >= 30: return "⭐ Platina"
        elif self.level >= 20: return "🥇 Ouro"
        elif self.level >= 10: return "🥈 Prata"
        elif self.level >= 5: return "🥉 Bronze"
        else: return "🎯 Iniciante"

    def check_month_reset(self):
        """Reset mensal: zera XP, level, inventário (mantém gold)"""
        now_month = datetime.now().strftime("%Y-%m")
        if self.current_month != now_month:
            if self.level > 0:
                trophy = Trophy(month=self.current_month, level=self.level)
                self.trophies.append(trophy)

            # Calcula espaço base do inventario (sem bolsa equipada)
            base_inventory = 6
            
            # Reset mensal
            self.xp = 0
            self.level = 0
            self.inventory = []           # limpa inventário
            self.max_inventory = base_inventory  # reseta para o base
            self.double_xp_active = False
            self.last_xp_lost = 0
            self.current_streak = 0
            self.perfect_streak = 0
            self.recent_completions = []  # limpa completions recentes
            self.daily_chest_claimed = None  # reseta baú diário
            self.expedition_active = False  # cancela expedição ativa
            self.expedition_start_time = None
            # gold permanece
            self.current_month = now_month
            return True
        return False
    
    def manual_reset(self):
        """Reset manual: reseta TUDO incluindo gold (não apaga tarefas)"""
        # Salva troféu se tiver level
        if self.level > 0:
            trophy = Trophy(month=self.current_month + "_manual", level=self.level)
            self.trophies.append(trophy)
        
        # Reseta tudo
        self.xp = 0
        self.gold = 0  # reseta gold também no reset manual
        self.level = 0
        self.inventory = []
        self.max_inventory = 6
        self.double_xp_active = False
        self.last_xp_lost = 0
        self.current_streak = 0
        self.perfect_streak = 0
        self.recent_completions = []
        self.daily_chest_claimed = None
        self.expedition_active = False
        self.expedition_start_time = None
        # Mantém badges e trophies

    def has_item(self, item_id: str) -> bool:
        return any(i.id == item_id for i in self.inventory)

    def add_item(self, item_id: str) -> bool:
        if len(self.inventory) >= self.max_inventory:
            return False

        config = ITEMS_CONFIG.get(item_id)
        if not config:
            return False

        item = Item(
            id=item_id,
            name=config["name"],
            emoji=config["emoji"],
            rarity=config["rarity"],
            item_type=config["type"],
            description=config["description"],
            sell_price=config["sell_price"]
        )
        self.inventory.append(item)
        return True

    def remove_item(self, item_id: str) -> bool:
        for i, item in enumerate(self.inventory):
            if item.id == item_id:
                self.inventory.pop(i)
                return True
        return False

    def add_badge(self, badge_id: str) -> Optional[Badge]:
        if any(b.id == badge_id for b in self.badges):
            return None

        config = AVAILABLE_BADGES.get(badge_id)
        if not config:
            return None

        badge = Badge(
            id=badge_id,
            name=config["name"],
            description=config["description"],
            emoji=config["emoji"],
            earned_at=datetime.now().isoformat()
        )
        self.badges.append(badge)
        return badge

    def update_streak(self, completion_time: str):
        """Atualiza streaks e verifica badge speed_demon (5 tarefas em 1 hora)"""
        today = datetime.now().strftime("%Y-%m-%d")

        if self.last_completion_date is None:
            self.current_streak = 1
        else:
            last_date = datetime.fromisoformat(self.last_completion_date).date()
            today_date = datetime.now().date()
            delta = (today_date - last_date).days

            if delta == 0:
                pass
            elif delta == 1:
                self.current_streak += 1
            else:
                self.current_streak = 1

        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak

        self.last_completion_date = today
        
        # Speed demon: adiciona timestamp e remove antigos (> 1 hora)
        self.recent_completions.append(completion_time)
        one_hour_ago = datetime.now().timestamp() - 3600
        self.recent_completions = [
            t for t in self.recent_completions 
            if datetime.fromisoformat(t).timestamp() > one_hour_ago
        ]


class TaskDB:
    def __init__(self, filename="tasks.json"):
        self.filename = filename
        self.tasks: List[Task] = []
        self.stats = UserStats()
        self.next_id = 1
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(t) for t in data.get('tasks', [])]
                    self.stats = UserStats.from_dict(data.get('stats', {}))
                    self.next_id = max([t.id for t in self.tasks], default=0) + 1
            except Exception as e:
                print(f"⚠️  Erro ao carregar dados: {e}")
                self.tasks = []
                self.stats = UserStats()
                self.next_id = 1

    def save(self):
        try:
            data = {
                'tasks': [t.to_dict() for t in self.tasks],
                'stats': self.stats.to_dict()
            }
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")

    def add_task(self, title: str, priority: str, category: str, due_date: str, due_time: str) -> Task:
        task = Task(
            id=self.next_id,
            title=title,
            priority=priority,
            category=category,
            due_date=due_date,
            due_time=due_time
        )
        self.next_id += 1
        self.tasks.append(task)
        self.save()
        return task

    def get_active_tasks(self) -> List[Task]:
        active = [t for t in self.tasks if not t.completed]
        priority_tasks = [t for t in active if t.is_priority]
        normal_tasks = [t for t in active if not t.is_priority]
        return priority_tasks + normal_tasks

    def get_completed_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.completed]

    def get_task(self, task_id: int) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == task_id), None)

    def update_task(self, task_id: int, **kwargs) -> Optional[Task]:
        task = self.get_task(task_id)
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            self.save()
        return task

    def toggle_task_priority(self, task_id: int) -> Optional[Task]:
        if not self.stats.has_item("coroa"):
            return None

        task = self.get_task(task_id)
        if task and not task.completed:
            task.is_priority = not task.is_priority
            self.save()
        return task

    def complete_task(self, task_id: int) -> Optional[Task]:
        task = self.get_task(task_id)
        if task and not task.completed:
            task.completed = True
            completion_time = datetime.now().isoformat()
            task.completed_at = completion_time

            # NOVOS VALORES V6.0: low=3, medium=5, high=7
            priority_xp = {"low": 3, "medium": 5, "high": 7}
            xp_earned = priority_xp.get(task.priority, 5)
            on_time = False

            if task.due_date and task.due_time:
                try:
                    due_datetime = datetime.fromisoformat(f"{task.due_date}T{task.due_time}")
                    if datetime.now() <= due_datetime:
                        on_time = True
                    else:
                        xp_earned = -xp_earned
                        self.stats.last_xp_lost = abs(xp_earned)
                        on_time = False
                except:
                    pass

            # Livro: +2 XP (novo valor V6.0)
            if self.stats.has_item("livro"):
                xp_earned += 2

            # Escudo: +2 proteção (novo valor V6.0)
            if self.stats.has_item("escudo") and xp_earned < 0:
                xp_earned += 2

            if self.stats.double_xp_active:
                xp_earned *= 2
                self.stats.double_xp_active = False

            gold_earned = 3

            # Livro: +1 Gold
            if self.stats.has_item("livro"):
                gold_earned += 1

            # Espada: +2 Gold (novo valor V6.0)
            if self.stats.has_item("espada"):
                gold_earned += 2

            if self.stats.has_item("coroa"):
                gold_earned *= 2

            task.xp_earned = xp_earned
            task.gold_earned = gold_earned
            task.on_time = on_time

            self.stats.check_month_reset()
            self.stats.xp += xp_earned
            self.stats.level = self.stats.xp // 100
            task.completed_level = self.stats.level
            self.stats.gold += gold_earned
            self.stats.total_completed += 1

            self.stats.update_streak(completion_time)

            if on_time:
                self.stats.perfect_streak += 1
            else:
                self.stats.perfect_streak = 0

            new_badges = []

            if self.stats.total_completed == 1:
                badge = self.stats.add_badge("first_task")
                if badge: new_badges.append(badge)

            if self.stats.current_streak == 3:
                badge = self.stats.add_badge("streak_3")
                if badge: new_badges.append(badge)
            elif self.stats.current_streak == 7:
                badge = self.stats.add_badge("streak_7")
                if badge: new_badges.append(badge)
            elif self.stats.current_streak == 30:
                badge = self.stats.add_badge("streak_30")
                if badge: new_badges.append(badge)

            if self.stats.perfect_streak == 10:
                badge = self.stats.add_badge("perfect_10")
                if badge: new_badges.append(badge)

            # Speed demon: 5 tarefas em 1 hora
            if len(self.stats.recent_completions) >= 5:
                badge = self.stats.add_badge("speed_demon")
                if badge: new_badges.append(badge)

            hour = datetime.now().hour
            if hour >= 22:
                badge = self.stats.add_badge("night_owl")
                if badge: new_badges.append(badge)
            elif hour < 6:
                badge = self.stats.add_badge("early_bird")
                if badge: new_badges.append(badge)

            if self.stats.total_completed == 100:
                badge = self.stats.add_badge("task_master")
                if badge: new_badges.append(badge)

            if self.stats.level == 10:
                badge = self.stats.add_badge("level_10")
                if badge: new_badges.append(badge)

            drop_item = self._roll_drop()

            if drop_item and len(self.stats.inventory) < self.stats.max_inventory:
                self.stats.add_item(drop_item)

            task.new_badges = new_badges
            task.drop_item = drop_item

            self.save()
        return task

    def _roll_drop(self) -> Optional[str]:
        """
        Sistema de drop com chances BALANCEADAS:
        pizza - 15%
        cafe - 15%
        cigarrinho - 10%
        bolsa - 3%
        livro - 3%
        espada - 3%
        escudo - 3%
        coroa - 0.5%

        Não dropa itens permanentes que o jogador já possui
        """
        roll = random.random()

        if roll < 0.15:
            return "pizza"
        elif roll < 0.30:
            return "cafe"
        elif roll < 0.40:
            return "cigarrinho"
        elif roll < 0.43:
            if not self.stats.has_item("bolsa"):
                return "bolsa"
            return None
        elif roll < 0.46:
            if not self.stats.has_item("livro"):
                return "livro"
            return None
        elif roll < 0.49:
            if not self.stats.has_item("espada"):
                return "espada"
            return None
        elif roll < 0.52:
            if not self.stats.has_item("escudo"):
                return "escudo"
            return None
        elif roll < 0.525:
            if not self.stats.has_item("coroa"):
                return "coroa"
            return None

        return None

    def activate_item(self, item_id: str) -> tuple:
        """Ativa/desativa efeito permanente de um item. Retorna (sucesso, mensagem, equipado)"""
        item = next((i for i in self.stats.inventory if i.id == item_id), None)
        if not item or item.item_type != "permanent":
            return False, "Item não encontrado ou não é permanente", False
        
        if item_id == "bolsa":
            if item.equipped:
                # Desativar bolsa
                self.stats.max_inventory -= 6
                item.equipped = False
                self.save()
                return True, "Bolsa Mística desequipada! Inventário reduzido em 6 slots.", False
            else:
                # Ativar bolsa
                self.stats.max_inventory += 6
                item.equipped = True
                self.save()
                return True, "Bolsa Mística equipada! +6 slots no inventário.", True
        
        # Para outros itens permanentes (livro, espada, escudo, coroa) - apenas toggle visual
        item.equipped = not item.equipped
        self.save()
        status = "equipado" if item.equipped else "desequipado"
        return True, f"{item.name} {status}!", item.equipped
    
    def get_equipped_items(self) -> List[str]:
        """Retorna lista de IDs dos itens equipados"""
        return [i.id for i in self.stats.inventory if getattr(i, 'equipped', False)]

    def restore_task(self, task_id: int) -> Optional[Task]:
        task = self.get_task(task_id)
        if task and task.completed:
            self.stats.xp -= task.xp_earned
            if self.stats.xp < 0:
                self.stats.xp = 0
            self.stats.gold -= task.gold_earned
            if self.stats.gold < 0:
                self.stats.gold = 0
            self.stats.level = self.stats.xp // 100

            task.completed = False
            task.completed_at = None
            task.completed_level = 0
            task.xp_earned = 0
            task.gold_earned = 0
            task.on_time = False

            self.save()
        return task

    def delete_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if task:
            self.tasks.remove(task)
            self.save()
            return True
        return False

    def clear_history(self) -> int:
        count = len([t for t in self.tasks if t.completed])
        self.tasks = [t for t in self.tasks if not t.completed]
        self.save()
        return count

    def get_overdue_tasks(self) -> List[Task]:
        return [t for t in self.get_active_tasks() if t.is_overdue()]

    def update_player_name(self, new_name: str) -> bool:
        if new_name.strip():
            self.stats.name = new_name.strip()
            self.save()
            return True
        return False
    
    def claim_daily_chest(self) -> tuple:
        """Baú diário: abre uma vez por dia com recompensas aleatórias"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Verifica se já abriu hoje
        if self.stats.daily_chest_claimed == today:
            return False, "Você já abriu o baú hoje! Volte amanhã.", None
        
        # Roll de recompensa (3% para cada prêmio especial)
        roll = random.random()
        
        if roll < 0.03:
            # 3% chance: 50 Gold
            self.stats.gold += 50
            reward_type = "gold"
            reward_value = 50
            message = "🎉 BAÚ DIÁRIO: Você encontrou 50 Gold!"
        elif roll < 0.06:
            # 3% chance: 50 XP
            self.stats.xp += 50
            self.stats.level = self.stats.xp // 100
            reward_type = "xp"
            reward_value = 50
            message = "🎉 BAÚ DIÁRIO: Você ganhou 50 XP!"
        else:
            # 94% chance: item aleatório (mesma taxa de drop das missões)
            drop_item = self._roll_drop()
            if drop_item and len(self.stats.inventory) < self.stats.max_inventory:
                self.stats.add_item(drop_item)
                item_config = ITEMS_CONFIG.get(drop_item, {})
                reward_type = "item"
                reward_value = item_config.get("name", drop_item)
                message = f"🎉 BAÚ DIÁRIO: Você encontrou {item_config.get('emoji', '🎁')} {item_config.get('name', 'um item')}!"
            else:
                # Se não puder pegar o item, dá gold compensatório
                self.stats.gold += 10
                reward_type = "gold"
                reward_value = 10
                message = "🎉 BAÚ DIÁRIO: Inventário cheio! Você recebeu 10 Gold compensatórios."
        
        self.stats.daily_chest_claimed = today
        self.save()
        return True, message, {"type": reward_type, "value": reward_value}
    
    def start_expedition(self) -> tuple:
        """Inicia expedição de 1 hora"""
        if self.stats.expedition_active:
            elapsed = datetime.now() - datetime.fromisoformat(self.stats.expedition_start_time)
            remaining = timedelta(hours=1) - elapsed
            minutes = int(remaining.total_seconds() / 60)
            return False, f"Expedição em andamento! Retorne em {minutes} minutos.", None
        
        self.stats.expedition_active = True
        self.stats.expedition_start_time = datetime.now().isoformat()
        self.save()
        return True, "🗺️ Expedição iniciada! Retorne em 1 hora para coletar recompensas.", None
    
    def complete_expedition(self) -> tuple:
        """Completa expedição e coleta recompensas"""
        if not self.stats.expedition_active:
            return False, "Nenhuma expedição em andamento.", None
        
        start_time = datetime.fromisoformat(self.stats.expedition_start_time)
        elapsed = datetime.now() - start_time
        
        if elapsed < timedelta(hours=1):
            remaining = timedelta(hours=1) - elapsed
            minutes = int(remaining.total_seconds() / 60)
            return False, f"Ainda faltam {minutes} minutos para completar a expedição!", None
        
        # Recompensa: 10 XP + 10 Gold
        self.stats.xp += 10
        self.stats.gold += 10
        self.stats.level = self.stats.xp // 100
        
        self.stats.expedition_active = False
        self.stats.expedition_start_time = None
        self.save()
        
        return True, "⚔️ Expedição completada! +10 XP, +10 Gold", {"xp": 10, "gold": 10}


# ============================================================
# Flask App Setup
# ============================================================

from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = "todo-dev-secret-isaac"
db = TaskDB()

# ============================================================
# Template Filters and Context Processors
# ============================================================

@app.context_processor
def inject_now():
    """Injeta função now() nos templates"""
    return {'now': datetime.now}

@app.template_filter('datetime_from_iso')
def datetime_from_iso_filter(iso_string):
    """Converte string ISO para datetime"""
    if not iso_string:
        return None
    try:
        return datetime.fromisoformat(iso_string)
    except (ValueError, TypeError):
        return None

# ============================================================
# Routes
# ============================================================

@app.route('/')
def index():
    db.stats.check_month_reset()
    active_tasks = db.get_active_tasks()
    completed_tasks = db.get_completed_tasks()
    overdue_tasks = db.get_overdue_tasks()

    categories = set([t.category for t in db.get_active_tasks()] + ['pessoal', 'interno', 'externo'])
    selected_category = request.args.get('category', 'all')

    if selected_category != 'all':
        active_tasks = [t for t in active_tasks if t.category == selected_category]

    return render_template_string(TEMPLATE,
        active_tasks=active_tasks,
        completed_tasks=completed_tasks,
        overdue_tasks=overdue_tasks,
        stats=db.stats,
        categories=sorted(list(categories)),
        selected_category=selected_category
    )

@app.route('/add', methods=['POST'])
def add_task():
    title = request.form.get('title', '').strip()
    priority = request.form.get('priority', 'low')
    category = request.form.get('category', 'pessoal')
    due_date = request.form.get('due_date', '')
    due_time = request.form.get('due_time', '')

    if not title:
        flash('⚠️ Título não pode estar vazio!', 'error')
        return redirect(url_for('index'))

    db.add_task(title, priority, category, due_date, due_time)
    flash('✅ Tarefa adicionada com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/manual-reset', methods=['POST'])
def manual_reset():
    """Rota para reset manual (reseta tudo incluindo gold)"""
    db.stats.manual_reset()
    db.save()
    flash('🔄 Reset manual realizado! Todos os status foram zerados.', 'info')
    return redirect(url_for('index'))

@app.route('/daily-chest')
def daily_chest():
    """Rota para abrir baú diário"""
    success, message, reward = db.claim_daily_chest()
    if success:
        flash(message, 'success')
    else:
        flash(message, 'info')
    return redirect(url_for('index'))

@app.route('/expedition-start')
def expedition_start():
    """Inicia expedição"""
    success, message, _ = db.start_expedition()
    if success:
        flash(message, 'success')
    else:
        flash(message, 'info')
    return redirect(url_for('index'))

@app.route('/expedition-complete')
def expedition_complete():
    """Completa expedição"""
    success, message, _ = db.complete_expedition()
    if success:
        flash(message, 'success')
    else:
        flash(message, 'info')
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id: int):
    task = db.complete_task(task_id)
    if task:
        xp_text = f"{task.xp_earned} XP"
        if task.on_time:
            xp_text += " ⭐"

        flash_msg = f'✅ Tarefa concluída! {xp_text} + {task.gold_earned} Gold'

        if db.stats.current_streak > 1:
            flash_msg += f' | 🔥 Streak: {db.stats.current_streak}'

        if hasattr(task, 'drop_item') and task.drop_item:
            item_config = ITEMS_CONFIG.get(task.drop_item, {})
            flash(f'🎁 Drop: {item_config.get("emoji", "")} {item_config.get("name", "")}!', 'success')

        if hasattr(task, 'new_badges') and task.new_badges:
            for badge in task.new_badges:
                flash(f'🎉 {badge.emoji} {badge.name}!', 'success')

        flash(flash_msg, 'success')
    return redirect(url_for('index'))

@app.route('/restore/<int:task_id>')
def restore_task(task_id: int):
    task = db.restore_task(task_id)
    if task:
        flash(f'♻️ Restaurada! (-{task.xp_earned} XP, -{task.gold_earned} Gold)', 'info')
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id: int):
    if db.delete_task(task_id):
        flash('🗑️ Tarefa removida', 'info')
    return redirect(url_for('index'))

@app.route('/priority/<int:task_id>')
def toggle_priority(task_id: int):
    if not db.stats.has_item("coroa"):
        flash('❌ Precisa da Coroa Certariana!', 'error')
        return redirect(url_for('index'))

    task = db.toggle_task_priority(task_id)
    if task:
        status = "⭐ Priorizada" if task.is_priority else "Normal"
        flash(f'✏️ Tarefa {status}!', 'info')
    return redirect(url_for('index'))

@app.route('/clear-history')
def clear_history():
    count = db.clear_history()
    flash(f'🗑️ Histórico limpo! ({count} tarefa(s))', 'success')
    return redirect(url_for('index'))

@app.route('/update-task/<int:task_id>', methods=['POST'])
def update_task_full(task_id: int):
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'low')
    category = request.form.get('category', 'pessoal')
    due_date = request.form.get('due_date', '')
    due_time = request.form.get('due_time', '')

    if not title:
        flash('⚠️ Título não pode estar vazio!', 'error')
        return redirect(url_for('index'))

    task = db.update_task(
        task_id,
        title=title,
        description=description,
        priority=priority,
        category=category,
        due_date=due_date,
        due_time=due_time
    )

    if task:
        flash('✏️ Tarefa atualizada!', 'success')

    return redirect(url_for('index'))

@app.route('/update-name', methods=['POST'])
def update_name():
    new_name = request.form.get('player_name', '').strip()
    if db.update_player_name(new_name):
        flash(f'👤 Nome: {new_name}!', 'success')
    else:
        flash('⚠️ Nome vazio!', 'error')
    return redirect(url_for('index'))

@app.route('/use-item/<item_id>', methods=['POST'])
def use_item(item_id: str):
    item = next((i for i in db.stats.inventory if i.id == item_id), None)

    if not item:
        flash('❌ Item não encontrado', 'error')
        return redirect(url_for('index'))

    used = False

    if item.item_type == "consumable":
        if item_id == "pizza":
            if db.stats.gold >= 2:
                db.stats.gold -= 2
                db.stats.xp += 2
                used = True
                flash('🪳 Pizza: -2 gold, +2 XP!', 'success')
            else:
                flash('❌ Sem gold suficiente!', 'error')

        elif item_id == "cigarrinho":
            if db.stats.last_xp_lost > 0:
                db.stats.xp += db.stats.last_xp_lost
                db.stats.last_xp_lost = 0
                used = True
                flash('🧃 Cigarrinho: XP restaurado!', 'success')
            else:
                flash('❌ Sem XP perdido para restaurar!', 'error')

        elif item_id == "cafe":
            db.stats.double_xp_active = True
            used = True
            flash('☕ Café: 2x XP próxima tarefa! ✨', 'info')

    elif item.item_type == "permanent":
        # Ativa/desativa item permanente com sistema de equipamento
        success, message, equipped = db.activate_item(item_id)
        if success:
            flash(message, 'success' if equipped else 'info')
            used = True
        else:
            flash(message, 'error')

    if used:
        if item.item_type == "consumable":
            db.stats.remove_item(item_id)
        db.save()

    return redirect(url_for('index'))

@app.route('/sell-item/<item_id>', methods=['POST'])
def sell_item(item_id: str):
    item = next((i for i in db.stats.inventory if i.id == item_id), None)

    if not item:
        flash('❌ Item não encontrado', 'error')
        return redirect(url_for('index'))

    sell_price = item.sell_price
    # Se o item estiver equipado, desequipar primeiro
    if getattr(item, 'equipped', False):
        if item_id == "bolsa":
            db.stats.max_inventory -= 6
        item.equipped = False

    db.stats.gold += sell_price
    db.stats.remove_item(item_id)
    db.save()

    flash(f'💰 Vendido: +{sell_price} Gold!', 'success')
    return redirect(url_for('index'))

@app.route('/api/inventory')
def api_inventory():
    return jsonify([i.to_dict() for i in db.stats.inventory])

@app.route('/api/badges')
def api_badges():
    return jsonify([{
        'id': b.id,
        'name': b.name,
        'description': b.description,
        'emoji': b.emoji,
        'earned_at': b.earned_at
    } for b in db.stats.badges])

@app.route('/api/stats')
def api_stats():
    return jsonify({
        'name': db.stats.name,
        'level': db.stats.level,
        'xp': db.stats.xp,
        'gold': db.stats.gold,
        'rank': db.stats.get_rank_title(),
        'current_streak': db.stats.current_streak,
        'best_streak': db.stats.best_streak,
        'total_completed': db.stats.total_completed,
        'perfect_streak': db.stats.perfect_streak,
        'badges_count': len(db.stats.badges),
        'trophies_count': len(db.stats.trophies),
        'inventory_count': len(db.stats.inventory),
        'max_inventory': db.stats.max_inventory
    })

@app.route('/api/trophies')
def api_trophies():
    return jsonify([{
        'month': t.month,
        'level': t.level,
        'emoji': t.get_trophy_emoji(),
        'earned_at': t.earned_at
    } for t in db.stats.trophies])

@app.route('/shop')
def shop():
    db.stats.check_month_reset()

    shop_items = []
    for item_id, config in ITEMS_CONFIG.items():
        if not db.stats.has_item(item_id) or config["type"] == "consumable":
            shop_items.append({
                'id': item_id,
                'name': config['name'],
                'emoji': config['emoji'],
                'rarity': config['rarity'],
                'description': config['description'],
                'shop_price': config.get('shop_price', config['sell_price'] * 5),
                'owned': db.stats.has_item(item_id),
                'type': config['type']
            })

    # Ordena por preço e, em caso de empate, pela ordem fixa (Cigarrinho antes do Café)
    shop_items.sort(
        key=lambda x: (
            x['shop_price'],
            ORDER_FIX.index(x['id']) if x['id'] in ORDER_FIX else 999
        )
    )

    return render_template_string(SHOP_TEMPLATE,
        stats=db.stats,
        shop_items=shop_items
    )

@app.route('/buy-item/<item_id>', methods=['POST'])
def buy_item(item_id: str):
    config = ITEMS_CONFIG.get(item_id)

    if not config:
        flash('❌ Item não encontrado!', 'error')
        return redirect(url_for('shop'))

    shop_price = config.get('shop_price', config['sell_price'] * 5)

    if db.stats.gold < shop_price:
        flash(f'❌ Gold insuficiente! Precisa de {shop_price - db.stats.gold} mais.', 'error')
        return redirect(url_for('shop'))

    if config['type'] == 'permanent' and db.stats.has_item(item_id):
        flash(f'❌ Você já possui este item!', 'error')
        return redirect(url_for('shop'))

    if len(db.stats.inventory) >= db.stats.max_inventory:
        flash(f'❌ Inventário cheio! ({db.stats.max_inventory}/{db.stats.max_inventory})', 'error')
        return redirect(url_for('shop'))

    db.stats.gold -= shop_price
    db.stats.add_item(item_id)
    db.save()

    flash(f'✅ Comprado! 💰 -{shop_price} Gold | 🎁 {config["emoji"]} {config["name"]}', 'success')
    return redirect(url_for('shop'))


# ============================================================
# HTML TEMPLATES
# ============================================================

SHOP_TEMPLATE = r"""<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>🏪 Loja - XP System V5.6</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { height: 100%; }
        body { font-family: system-ui, -apple-system, sans-serif; background: #0b0f19; color: #e7eaf0; line-height: 1.6; }
        .wrap { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #121a2b 0%, #1a2a3f 100%); border: 1px solid #243252; border-radius: 14px; padding: 20px; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3); display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 28px; margin: 0; }
        .header-stats { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
        .stat-badge { background: #2b63ff; padding: 10px 16px; border-radius: 8px; font-weight: 600; }
        .back-btn { background: #2a3a60; border: none; color: white; padding: 11px 16px; border-radius: 10px; cursor: pointer; font-weight: 600; text-decoration: none; display: inline-block; }
        .back-btn:hover { background: #3a4a70; }
        .section-title { font-size: 18px; font-weight: 700; margin: 24px 0 16px 0; display: flex; align-items: center; gap: 10px; }
        .shop-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 32px; }
        .shop-card { background: #121a2b; border: 2px solid #243252; border-radius: 14px; padding: 16px; transition: all 0.3s ease; display: flex; flex-direction: column; }
        .shop-card:hover { border-color: #2b63ff; box-shadow: 0 10px 30px rgba(43, 99, 255, 0.2); transform: translateY(-4px); }
        .shop-card.epic { border-color: #8b5cf6; }
        .shop-card.legendary { border-color: #ffd60a; }
        .card-header { display: flex; justify-content: space-between; align-items: start; gap: 12px; margin-bottom: 12px; }
        .card-title { font-weight: 700; font-size: 16px; flex: 1; }
        .card-rarity { padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .rarity-common { background: rgba(52, 199, 89, 0.2); color: #34c759; }
        .rarity-rare { background: rgba(43, 99, 255, 0.2); color: #2b63ff; }
        .rarity-epic { background: rgba(139, 92, 246, 0.2); color: #8b5cf6; }
        .rarity-legendary { background: rgba(255, 214, 10, 0.2); color: #ffd60a; }
        .card-emoji { font-size: 32px; margin-bottom: 8px; }
        .card-description { font-size: 13px; color: #a8b5c8; margin-bottom: 12px; line-height: 1.4; }
        .card-price { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .price-label { font-size: 12px; opacity: 0.8; }
        .price-value { font-size: 20px; font-weight: 700; color: #ffd60a; }
        .card-action { display: flex; gap: 8px; margin-top: auto; }
        button.buy { background: #34c759; border: none; color: white; padding: 11px 16px; border-radius: 10px; cursor: pointer; font-weight: 600; flex: 1; transition: all 0.2s ease; }
        button.buy:hover { background: #2ba651; }
        button.buy:disabled { background: #2a3a60; cursor: not-allowed; opacity: 0.5; }
        button.owned { background: #2a3a60; color: #a8b5c8; cursor: not-allowed; }
        .flash { padding: 12px 16px; border-radius: 10px; margin-bottom: 16px; font-weight: 600; border-left: 4px solid; }
        .flash.success { background: rgba(52, 199, 89, 0.1); border-color: #34c759; color: #34c759; }
        .flash.error { background: rgba(183, 47, 74, 0.1); border-color: #b72f4a; color: #b72f4a; }
        .filter-tabs { display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }
        .filter-btn { background: #2a3a60; border: 2px solid transparent; color: #e7eaf0; padding: 10px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.2s ease; }
        .filter-btn:hover { border-color: #2b63ff; }
        .filter-btn.active { background: #2b63ff; border-color: #2b63ff; }
        @media (max-width: 768px) { .header { flex-direction: column; align-items: flex-start; gap: 16px; } .header-stats { width: 100%; flex-wrap: wrap; } .shop-grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="wrap">
        <div class="header">
            <h1>🏪 Loja Certariana</h1>
            <div style="display: flex; gap: 16px; align-items: center; flex-wrap: wrap;">
                <div class="header-stats">
                    <div class="stat-badge">💰 {{ stats.gold }} Gold</div>
                    <div class="stat-badge">🎒 {{ stats.inventory|length }}/{{ stats.max_inventory }}</div>
                </div>
                <a href="{{ url_for('index') }}" class="back-btn">← Voltar</a>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}{% for category, message in messages %}<div class="flash {{ category }}">{{ message }}</div>{% endfor %}{% endwith %}

        <div class="filter-tabs">
            <button class="filter-btn active" onclick="filterShop('all')">Todos ({{ shop_items|length }})</button>
            <button class="filter-btn" onclick="filterShop('consumable')">🧪 Consumíveis</button>
            <button class="filter-btn" onclick="filterShop('permanent')">⭐ Permanentes</button>
            <button class="filter-btn" onclick="filterShop('epic')">💎 Épicos</button>
            <button class="filter-btn" onclick="filterShop('legendary')">👑 Lendários</button>
        </div>

        <div class="section-title">📦 Disponíveis na Loja</div>

        {% if shop_items %}
            <div class="shop-grid" id="shopGrid">
                {% for item in shop_items %}
                    <div class="shop-card rarity-{{ item.rarity }}" data-rarity="{{ item.rarity }}" data-type="{{ item.type }}">
                        <div class="card-header">
                            <div>
                                <div class="card-emoji">{{ item.emoji }}</div>
                                <div class="card-title">{{ item.name }}</div>
                            </div>
                            <span class="card-rarity rarity-{{ item.rarity }}">{{ item.rarity }}</span>
                        </div>
                        <p class="card-description">{{ item.description }}</p>
                        <div class="card-price">
                            <span class="price-label">Preço:</span>
                            <span class="price-value">{{ item.shop_price }} G</span>
                        </div>
                        <div class="card-action">
                            {% if item.owned and item.type == 'permanent' %}
                                <button class="buy owned" disabled>✅ Possui</button>
                            {% else %}
                                <form method="post" action="{{ url_for('buy_item', item_id=item.id) }}" style="flex: 1;">
                                    <button type="submit" class="buy" {% if stats.gold < item.shop_price %}disabled{% endif %}>
                                        {% if stats.gold < item.shop_price %}❌ Sem gold{% else %}🛒 Comprar{% endif %}
                                    </button>
                                </form>
                            {% endif %}
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <div style="text-align: center; padding: 40px; color: #5a6b7f; background: #121a2b; border-radius: 14px; border: 1px solid #243252;">
                ✨ Todos os itens foram comprados! Que incrível!
            </div>
        {% endif %}

        <div style="margin-top: 32px; padding: 16px; background: #121a2b; border: 1px solid #243252; border-radius: 14px; text-align: center; color: #a8b5c8;">
            <div style="font-size: 12px; opacity: 0.7; margin-bottom: 8px;">💡 Dica:</div>
            <div style="font-size: 13px;">Itens na loja custam <strong>5x o preço de venda</strong>. Complete tarefas e junte gold para suas compras! 💪</div>
        </div>
    </div>

    <script>
        function filterShop(type) {
            const cards = document.querySelectorAll('.shop-card');
            const buttons = document.querySelectorAll('.filter-btn');

            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            cards.forEach(card => {
                if (type === 'all') {
                    card.style.display = 'flex';
                } else {
                    card.style.display = (card.dataset.rarity === type || card.dataset.type === type) ? 'flex' : 'none';
                }
            });
        }
    </script>
</body>
</html>"""


TEMPLATE = r"""<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>📝 Minhas Tarefas - XP System V6.0</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { height: 100%; }
        body { font-family: system-ui, -apple-system, sans-serif; background: #0b0f19; color: #e7eaf0; line-height: 1.6; }
        .wrap { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #121a2b 0%, #1a2a3f 100%); border: 1px solid #243252; border-radius: 14px; padding: 20px; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3); }
        .header-top { display: flex; justify-content: space-between; align-items: center; gap: 20px; flex-wrap: wrap; margin-bottom: 16px; }
        .user-info { display: flex; align-items: center; gap: 12px; }
        .user-info h1 { font-size: 28px; font-weight: 700; margin-bottom: 0; }
        .user-info-sub { display: flex; flex-direction: column; }
        .level-info { font-size: 14px; opacity: 0.85; color: #a8b5c8; }
        .user-controls { display: flex; gap: 8px; }
        .btn-icon { background: #2b63ff; border: none; color: white; width: 36px; height: 36px; border-radius: 8px; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease; }
        .btn-icon:hover { background: #1e4fd4; transform: scale(1.1); }
        .badges-display { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        .badge-pill { background: #2b63ff; padding: 6px 12px; border-radius: 999px; font-weight: 600; font-size: 13px; display: flex; align-items: center; gap: 6px; }
        .xp-bar-container { width: 100%; max-width: 400px; background: #0d1424; border: 1px solid #2a3a60; border-radius: 12px; overflow: hidden; height: 28px; position: relative; }
        .xp-bar-fill { background: linear-gradient(90deg, #2b63ff, #00d4ff); height: 100%; transition: width 0.3s ease; }
        .xp-bar-label { position: absolute; width: 100%; text-align: center; font-size: 12px; font-weight: 600; color: #e7eaf0; line-height: 28px; }
        .collapsible-section { margin-bottom: 20px; background: #121a2b; border: 1px solid #243252; border-radius: 14px; overflow: hidden; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25); }
        .section-header { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: linear-gradient(135deg, #121a2b 0%, #1a2a3f 100%); border-bottom: 1px solid #243252; cursor: pointer; transition: all 0.2s ease; }
        .section-header:hover { background: linear-gradient(135deg, #1a2a3f 0%, #243252 100%); }
        .section-header h2 { font-size: 16px; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 10px; }
        .section-toggle { font-size: 20px; transition: transform 0.3s ease; color: #2b63ff; }
        .section-toggle.collapsed { transform: rotate(-90deg); }
        .section-content { padding: 16px; max-height: 10000px; overflow: hidden; transition: max-height 0.3s ease, padding 0.3s ease; }
        .section-content.collapsed { max-height: 0; padding: 0 16px; }
        .card { background: #121a2b; border: 1px solid #243252; border-radius: 14px; padding: 16px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25); }
        .form-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 12px; }
        .form-group { display: flex; flex-direction: column; }
        label { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #a8b5c8; margin-bottom: 6px; letter-spacing: 0.5px; }
        input[type="text"], input[type="date"], input[type="time"], select, textarea { background: #0d1424; border: 1px solid #2a3a60; border-radius: 10px; color: #e7eaf0; padding: 10px 12px; font-family: inherit; font-size: 14px; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #2b63ff; box-shadow: 0 0 0 3px rgba(43, 99, 255, 0.1); }
        button, a.btn { background: #2b63ff; border: none; color: white; padding: 11px 16px; border-radius: 10px; cursor: pointer; font-weight: 600; font-size: 13px; text-decoration: none; display: inline-block; transition: all 0.2s ease; }
        button:hover, a.btn:hover { background: #1e4fd4; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(43, 99, 255, 0.3); }
        button.secondary { background: #2a3a60; color: #e7eaf0; }
        button.secondary:hover { background: #3a4a70; }
        button.success { background: #34c759; }
        button.success:hover { background: #2ba651; }
        button.danger { background: #b72f4a; }
        button.danger:hover { background: #a01d38; }
        button.warning { background: #ff9500; }
        button.warning:hover { background: #e68900; }
        button.info { background: #8b5cf6; }
        button.info:hover { background: #7c3aed; }
        .task-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
        .task-card { background: #0d1424; border: 1px solid #2a3a60; border-left: 4px solid; border-radius: 10px; padding: 14px; transition: all 0.2s ease; min-height: 120px; display: flex; flex-direction: column; }
        .task-card:hover { border-color: #3a4a70; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3); }
        .task-card.priority { border: 2px solid #ffd60a; background: linear-gradient(135deg, rgba(255, 214, 10, 0.1), transparent); }
        .task-card.priority-low { border-left-color: #34c759; }
        .task-card.priority-medium { border-left-color: #ffd60a; }
        .task-card.priority-high { border-left-color: #ff6b35; }
        .task-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 8px; }
        .task-title { font-weight: 600; font-size: 14px; color: #e7eaf0; flex: 1; }
        .task-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-top: auto; }
        .task-actions button { flex: 1; min-width: 50px; padding: 8px 10px; font-size: 11px; }
        .flash { padding: 12px 16px; border-radius: 10px; margin-bottom: 16px; font-weight: 600; border-left: 4px solid; }
        .flash.success { background: rgba(52, 199, 89, 0.1); border-color: #34c759; color: #34c759; }
        .flash.error { background: rgba(183, 47, 74, 0.1); border-color: #b72f4a; color: #b72f4a; }
        .flash.info { background: rgba(43, 99, 255, 0.1); border-color: #2b63ff; color: #2b63ff; }
        .modal { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.7); z-index: 1000; align-items: center; justify-content: center; }
        .modal.active { display: flex; }
        .modal-content { background: #121a2b; border: 1px solid #243252; border-radius: 14px; padding: 24px; max-width: 600px; width: 90%; max-height: 90vh; overflow-y: auto; }
        .modal-header { font-size: 18px; font-weight: 700; margin-bottom: 20px; color: #e7eaf0; display: flex; justify-content: space-between; align-items: center; }
        .modal-close { cursor: pointer; font-size: 24px; color: #a8b5c8; background: none; border: none; padding: 0; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; }
        .modal-close:hover { color: #e7eaf0; }
        @media (max-width: 768px) { .form-row { grid-template-columns: 1fr; } .header-top { flex-direction: column; align-items: flex-start; } .task-list { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="wrap">
        <div class="header">
            <div class="header-top">
                <div class="user-info">
                    <div class="user-info-sub">
                        <h1>📝 {{ stats.name }}</h1>
                        <div class="level-info">{{ stats.get_rank_title() }} • Nível {{ stats.level }}</div>
                    </div>
                    <div class="user-controls">
                        <button class="btn-icon" onclick="openNameModal()" title="Nome">👤</button>
                        <button class="btn-icon" onclick="openInventoryModal()" title="Inventário">🎒</button>
                        <button class="btn-icon" onclick="location.href='{{ url_for('shop') }}'" title="Loja">🏪</button>
                        <button class="btn-icon" onclick="openStatsModal()" title="Stats">📊</button>
                        <button class="btn-icon" onclick="openSettingsModal()" title="Configurações">⚙️</button>
                    </div>
                </div>
                <div class="badges-display">
                    <div class="badge-pill">💰 {{ stats.gold }} Gold</div>
                    <div class="badge-pill">⭐ {{ stats.xp }} XP</div>
                    {% if stats.current_streak > 0 %}<div class="badge-pill">🔥 {{ stats.current_streak }} dias</div>{% endif %}
                </div>
            </div>
            <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px;">
                    <label style="display: block; margin-bottom: 4px; font-size: 12px; opacity: 0.8;">{{ stats.get_xp_for_level() }}/100 XP</label>
                    <div class="xp-bar-container">
                        <div class="xp-bar-fill" style="width: {{ stats.get_progress_percent() }}%"></div>
                        <span class="xp-bar-label">{{ stats.get_progress_percent() }}%</span>
                    </div>
                </div>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}{% for category, message in messages %}<div class="flash {{ category }}">{{ message }}</div>{% endfor %}{% endwith %}

        <div class="collapsible-section">
            <div class="section-header" onclick="toggleSection(this, 'nova-tarefa')">
                <h2>➕ Nova Tarefa</h2>
                <span class="section-toggle collapsed">▼</span>
            </div>
            <div class="section-content collapsed" data-section="nova-tarefa">
                <div class="card">
                    <form method="post" action="{{ url_for('add_task') }}">
                        <div class="form-row" style="grid-template-columns: 1fr;">
                            <div class="form-group"><label>Título</label><input type="text" name="title" placeholder="Ex: Corrigir bug..." required></div>
                        </div>
                        <div class="form-row">
                            <div class="form-group"><label>Prioridade</label><select name="priority"><option value="low">🟢 Baixa</option><option value="medium" selected>🟡 Média</option><option value="high">🔴 Urgente</option></select></div>
                            <div class="form-group"><label>Categoria</label><select name="category"><option value="pessoal">👤 Pessoal</option><option value="interno">🏢 Interno</option><option value="externo">📞 Externo</option></select></div>
                            <div class="form-group"><label>Data</label><input type="date" name="due_date"></div>
                        </div>
                        <div class="form-row" style="grid-template-columns: 1fr;">
                            <div class="form-group"><label>Hora</label><input type="time" name="due_time" id="defaultTime"></div>
                        </div>
                        <button type="submit" style="width: 100%;">✅ Adicionar</button>
                    </form>
                </div>
            </div>
        </div>

        <div class="collapsible-section">
            <div class="section-header" onclick="toggleSection(this, 'tarefas-ativas')">
                <h2>⏳ Tarefas Ativas ({{ active_tasks|length }})</h2>
                <span class="section-toggle collapsed">▼</span>
            </div>
            <div class="section-content collapsed" data-section="tarefas-ativas">
                <div style="padding: 0 16px;">
                    {% if active_tasks %}
                        <div class="task-list">
                            {% for task in active_tasks %}
                                <div class="task-card priority-{{ task.priority }}{% if task.is_priority %} priority{% endif %}">
                                    <div class="task-header"><div class="task-title">{{ task.title }}{% if task.is_priority %} ⭐{% endif %}</div></div>
                                    <div style="font-size: 12px; color: #a8b5c8; margin-bottom: 8px;">{% if task.due_date %}{{ task.due_date }} {{ task.due_time }}{% endif %}</div>
                                    <div class="task-actions" style="margin-top: auto;">
                                        <button class="secondary" onclick="openEditModal({{ task.id }}, '{{ task.title }}', '{{ task.priority }}', '{{ task.category }}', '{{ task.due_date }}', '{{ task.due_time }}', '{{ task.description }}')">✏️ Editar</button>
                                        <button class="success" onclick="location.href='{{ url_for('complete_task', task_id=task.id) }}'">✅ OK</button>
                                        {% if stats.has_item('coroa') %}<button class="warning" onclick="location.href='{{ url_for('toggle_priority', task_id=task.id) }}'" title="Prioridade">⭐ Prior</button>{% endif %}
                                        <button class="danger" onclick="if(confirm('Deletar?')) location.href='{{ url_for('delete_task', task_id=task.id) }}'">🗑️ Del</button>
                                    </div>
                                </div>
                            {% endfor %}
                        </div>
                    {% else %}
                        <div style="text-align: center; padding: 40px; color: #5a6b7f;">✨ Sem tarefas!</div>
                    {% endif %}
                </div>
            </div>
        </div>

        {% if completed_tasks %}
            <div class="collapsible-section">
                <div class="section-header" onclick="toggleSection(this, 'historico')">
                    <h2>🏆 Histórico ({{ completed_tasks|length }})</h2>
                    <span class="section-toggle collapsed">▼</span>
                </div>
                <div class="section-content collapsed" data-section="historico">
                    <div style="padding: 0 16px;">
                        <button class="warning" onclick="if(confirm('Limpar?')) location.href='{{ url_for('clear_history') }}'" style="margin-bottom: 16px;">🗑️ Limpar</button>
                        <div class="task-list">
                            {% for task in completed_tasks|reverse %}
                                <div class="task-card" style="border-left-color: #2b63ff;">
                                    <div style="font-weight: 600;">{{ task.title }}</div>
                                    <div style="font-size: 12px; color: #a8b5c8; margin: 8px 0;">{{ task.xp_earned }} XP • {{ task.gold_earned }} Gold</div>
                                    <div class="task-actions" style="margin-top: auto;">
                                        <button class="secondary" onclick="location.href='{{ url_for('restore_task', task_id=task.id) }}'">♻️ Rest</button>
                                        <button class="danger" onclick="if(confirm('Deletar?')) location.href='{{ url_for('delete_task', task_id=task.id) }}'">🗑️ Del</button>
                                    </div>
                                </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        {% endif %}
    </div>

    <div class="modal" id="nameModal">
        <div class="modal-content">
            <div class="modal-header"><div>👤 Nome</div><button class="modal-close" onclick="closeNameModal()">&times;</button></div>
            <form method="post" action="{{ url_for('update_name') }}">
                <div class="form-row" style="grid-template-columns: 1fr;">
                    <div class="form-group"><label>Novo Nome</label><input type="text" name="player_name" value="{{ stats.name }}" required></div>
                </div>
                <button type="submit" class="success" style="width: 100%;">💾 Salvar</button>
            </form>
        </div>
    </div>

    <div class="modal" id="inventoryModal">
        <div class="modal-content" style="max-width: 800px;">
            <div class="modal-header"><div>🎒 Inventário (<span id="inventoryCount">0</span>/{{ stats.max_inventory }})</div><button class="modal-close" onclick="closeInventoryModal()">&times;</button></div>
            <div id="inventoryContent" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;"></div>
        </div>
    </div>

    <div class="modal" id="statsModal">
        <div class="modal-content">
            <div class="modal-header"><div>📊 Estatísticas</div><button class="modal-close" onclick="closeStatsModal()">&times;</button></div>
            <div id="statsContent" style="display: grid; gap: 12px;"></div>
        </div>
    </div>

    <div class="modal" id="editModal">
        <div class="modal-content">
            <div class="modal-header"><div>✏️ Editar Tarefa</div><button class="modal-close" onclick="closeEditModal()">&times;</button></div>
            <form method="post" id="editForm">
                <div class="form-row" style="grid-template-columns: 1fr;">
                    <div class="form-group"><label>Título</label><input type="text" name="title" id="editTitle" required></div>
                </div>
                <div class="form-row" style="grid-template-columns: 1fr;">
                    <div class="form-group"><label>Observações</label><textarea name="description" id="editDescription" rows="3" placeholder="Detalhes da tarefa..."></textarea></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Prioridade</label><select name="priority" id="editPriority"><option value="low">🟢 Baixa</option><option value="medium">🟡 Média</option><option value="high">🔴 Urgente</option></select></div>
                    <div class="form-group"><label>Categoria</label><select name="category" id="editCategory"><option value="pessoal">👤 Pessoal</option><option value="interno">🏢 Interno</option><option value="externo">📞 Externo</option></select></div>
                    <div class="form-group"><label>Data</label><input type="date" name="due_date" id="editDueDate"></div>
                </div>
                <div class="form-row" style="grid-template-columns: 1fr;">
                    <div class="form-group"><label>Hora</label><input type="time" name="due_time" id="editDueTime"></div>
                </div>
                <button type="submit" class="success" style="width: 100%;">💾 Salvar</button>
            </form>
        </div>
    </div>

    <div class="modal" id="settingsModal">
        <div class="modal-content">
            <div class="modal-header"><div>⚙️ Configurações</div><button class="modal-close" onclick="closeSettingsModal()">&times;</button></div>
            <div style="display: grid; gap: 16px;">
                <div class="card" style="padding: 16px;">
                    <h3 style="margin-bottom: 12px; font-size: 16px;">🎮 Game</h3>
                    <div style="display: grid; gap: 8px;">
                        <a href="{{ url_for('daily_chest') }}" class="btn" style="display: block; text-align: center; background: #8b5cf6; color: white; padding: 11px 16px; border-radius: 10px; text-decoration: none; font-weight: 600;">🎁 Baú Diário</a>
                        {% if stats.expedition_active %}
                            {% set elapsed = (now() - stats.expedition_start_time|datetime_from_iso).seconds // 60 if stats.expedition_start_time else 0 %}
                            {% if elapsed >= 60 %}
                                <a href="{{ url_for('expedition_complete') }}" class="btn" style="display: block; text-align: center; background: #34c759; color: white; padding: 11px 16px; border-radius: 10px; text-decoration: none; font-weight: 600;">⚔️ Coletar Expedição</a>
                            {% else %}
                                <button disabled style="display: block; width: 100%; text-align: center; background: #2a3a60; color: #a8b5c8; padding: 11px 16px; border-radius: 10px; cursor: not-allowed;">⏳ Expedição em andamento...</button>
                            {% endif %}
                        {% else %}
                            <a href="{{ url_for('expedition_start') }}" class="btn" style="display: block; text-align: center; background: #ff9500; color: white; padding: 11px 16px; border-radius: 10px; text-decoration: none; font-weight: 600;">🗺️ Iniciar Expedição (1h)</a>
                        {% endif %}
                    </div>
                </div>
                <div class="card" style="padding: 16px;">
                    <h3 style="margin-bottom: 12px; font-size: 16px; color: #b72f4a;">⚠️ Zona de Perigo</h3>
                    <form method="post" action="{{ url_for('manual_reset') }}" onsubmit="return confirm('TEM CERTEZA? Isso vai resetar TODO seu progresso (XP, Gold, Itens, Level). Tarefas NÃO serão apagadas.')">
                        <button type="submit" class="danger" style="width: 100%;">🔄 Reset Manual Completo</button>
                    </form>
                    <p style="font-size: 12px; color: #a8b5c8; margin-top: 8px;">O reset mensal mantém o Gold. O reset manual reseta TUDO.</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function toggleSection(e,t){const c=e.nextElementSibling,o=e.querySelector('.section-toggle');c.classList.toggle('collapsed'),o.classList.toggle('collapsed'),localStorage.setItem('section-'+t,c.classList.contains('collapsed')?'collapsed':'expanded')}function restoreSectionStates(){['nova-tarefa','tarefas-ativas','historico'].forEach(e=>{if('expanded'===localStorage.getItem('section-'+e)){const t=document.querySelector(`[data-section="${e}"]`);t&&(t.classList.remove('collapsed'),t.previousElementSibling.querySelector('.section-toggle').classList.remove('collapsed'))}})}function openNameModal(){document.getElementById('nameModal').classList.add('active')}function closeNameModal(){document.getElementById('nameModal').classList.remove('active')}function openInventoryModal(){document.getElementById('inventoryModal').classList.add('active'),loadInventory()}function closeInventoryModal(){document.getElementById('inventoryModal').classList.remove('active')}function openStatsModal(){document.getElementById('statsModal').classList.add('active'),loadStats()}function closeStatsModal(){document.getElementById('statsModal').classList.remove('active')}function openSettingsModal(){document.getElementById('settingsModal').classList.add('active')}function closeSettingsModal(){document.getElementById('settingsModal').classList.remove('active')}function loadInventory(){fetch('/api/inventory').then(e=>e.json()).then(e=>{document.getElementById('inventoryCount').textContent=e.length;let t='<div><h3 style="margin-bottom: 12px;">🎒 Items</h3>';e.length?e.forEach(e=>{const isEquipped=e.equipped||false;const borderStyle=isEquipped?'border: 2px solid #FFD700;':'';const btnText='permanent'===e.item_type?(isEquipped?'Desequipar':'Equipar'):('consumable'===e.item_type?'Usar':'');const btnClass='permanent'===e.item_type?(isEquipped?'warning':'info'):('consumable'===e.item_type?'success':'');const i='permanent'===e.item_type?`<form method="post" action="/use-item/${e.id}" style="flex: 1;"><button type="submit" class="${btnClass}" style="width: 100%; padding: 6px;">${btnText}</button></form>`:'consumable'===e.item_type?`<form method="post" action="/use-item/${e.id}" style="flex: 1;"><button type="submit" class="${btnClass}" style="width: 100%; padding: 6px;">${btnText}</button></form>`:'';t+=`<div class="card" style="margin-bottom: 8px; padding: 12px; ${borderStyle}"><div style="font-weight: 600;">${e.emoji} ${e.name}</div><div style="font-size: 12px; opacity: 0.7; margin: 4px 0;">${e.rarity}</div><div style="font-size: 13px; color: #a8b5c8;">${e.description}</div><div style="display: flex; gap: 8px; margin-top: 8px;">${i}<form method="post" action="/sell-item/${e.id}" style="flex: 1;"><button type="submit" class="warning" style="width: 100%; padding: 6px;">Vender ${e.sell_price}G</button></form></div></div>`}):t+='<p style="opacity: 0.7;">Inventário vazio</p>',t+='</div>',document.getElementById('inventoryContent').innerHTML=t})}function loadStats(){fetch('/api/stats').then(e=>e.json()).then(e=>{document.getElementById('statsContent').innerHTML=`<div class="card" style="padding: 16px; text-align: center;"><div style="font-size: 24px; font-weight: 700; margin-bottom: 8px;">${e.rank}</div><div>Nível ${e.level} • ${e.xp} XP</div></div><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;"><div class="card" style="padding: 16px; text-align: center;"><div style="font-size: 28px; margin-bottom: 4px;">🔥</div><div style="font-size: 20px; font-weight: 700;">${e.current_streak}</div><div style="font-size: 12px; opacity: 0.7;">Streak</div></div><div class="card" style="padding: 16px; text-align: center;"><div style="font-size: 28px; margin-bottom: 4px;">✅</div><div style="font-size: 20px; font-weight: 700;">${e.total_completed}</div><div style="font-size: 12px; opacity: 0.7;">Concluídas</div></div><div class="card" style="padding: 16px; text-align: center;"><div style="font-size: 28px; margin-bottom: 4px;">🎒</div><div style="font-size: 20px; font-weight: 700;">${e.inventory_count}/${e.max_inventory}</div><div style="font-size: 12px; opacity: 0.7;">Inventário</div></div></div>`})}function openEditModal(e,t,i,a,l,s,d){document.getElementById('editTitle').value=t,document.getElementById('editPriority').value=i||'low',document.getElementById('editCategory').value=a||'pessoal',document.getElementById('editDueDate').value=l||'',document.getElementById('editDueTime').value=s||'',document.getElementById('editDescription').value=d||'',document.getElementById('editForm').action='/update-task/'+e,document.getElementById('editModal').classList.add('active')}function closeEditModal(){document.getElementById('editModal').classList.remove('active')}document.getElementById('nameModal')?.addEventListener('click',function(e){e.target===this&&closeNameModal()}),document.getElementById('inventoryModal')?.addEventListener('click',function(e){e.target===this&&closeInventoryModal()}),document.getElementById('statsModal')?.addEventListener('click',function(e){e.target===this&&closeStatsModal()}),document.getElementById('editModal')?.addEventListener('click',function(e){e.target===this&&closeEditModal()}),document.getElementById('settingsModal')?.addEventListener('click',function(e){e.target===this&&closeSettingsModal()}),window.addEventListener('load',restoreSectionStates);
        
        // Preenche hora atual automaticamente no campo de hora
        window.addEventListener('load', function() {
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const timeInput = document.getElementById('defaultTime');
            if (timeInput) {
                timeInput.value = `${hours}:${minutes}`;
            }
        });
    </script>
</body>
</html>"""

if __name__ == '__main__':
    dep_manager = DependencyManager()
    dep_manager.print_banner()

    if not dep_manager.check_python_version():
        sys.exit(1)
    if not dep_manager.ensure_pip():
        sys.exit(1)
    if not dep_manager.install_all():
        print("\n⚠️  Algumas dependências falharam, mas tentando continuar...")
    if not dep_manager.verify_imports():
        print("❌ Erro crítico: não consegui importar dependências necessárias")
        sys.exit(1)

    port = 5001
    url = f"http://localhost:{port}"

    print("\n" + "="*60)
    print("🚀 INICIANDO TODO APP V6.0")
    print("="*60)
    print(f"🌐 URL: {url}")
    print(f"📊 Dados: tasks.json")
    print(f"🎮 Game: Baú Diário e Expedição!")
    print(f"⚙️  Configurações com Reset Manual!")
    print(f"🕐 Hora automática no campo de tarefa!")
    print(f"🖥️  Abrindo navegador...\n")

    webbrowser.open(url)
    print("✅ Servidor iniciado em:", url)
    print("💡 Ctrl+C para parar\n")

    app.run(debug=True, port=port, use_reloader=False)
