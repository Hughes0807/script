import os
import json
import time
import cv2
import numpy as np
import pyautogui
import pytesseract
import winsound
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageGrab, ImageTk, ImageDraw
from datetime import datetime

# 创建必要的目录
os.makedirs("images", exist_ok=True)
os.makedirs("config", exist_ok=True)

# 图片识别基础信息：战斗界面、结束界面、材料界面
FIGHT_REGION = (1334, 774, 413, 237)
FIGHT_IMAGE_PATH = "images/fight.png"
OVER_REGION = (697, 364, 522, 384)
OVER_IMAGE_PATH = "images/over.png"
MATERIALS_REGION = (1033, 371, 191, 377)
MATERIALS_IMAGE_PATH = "images/materials.png"

class MonsterFarmApp:
    def __init__(self, root):
        self.root = root
        self.root.title("野怪整合脚本")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f7f2f7')

        # 应用样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f7f2f7')
        self.style.configure('TLabel', background='#f7f2f7', foreground='#000000')
        self.style.configure('TButton', background='#978697', foreground='#f7f2f7')
        self.style.map('TButton', background=[('active', '#413941')])
        self.style.configure('Treeview', background='#E4D2E4', foreground='#000000', fieldbackground='#E4D2E4')
        self.style.map('Treeview', background=[('selected', '#978697')])
        self.style.configure('Treeview.Heading', background='#f7f2f7', foreground='#000000')
        self.style.configure('TNotebook', background='#f7f2f7')
        self.style.configure('TNotebook.Tab', background='#E4D2E4', foreground='#000000', padding=[10, 5])
        self.style.map('TNotebook.Tab', background=[('selected', '#978697')])

        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        # 创建标签页
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        # 创建配置管理标签页
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="配置管理")
        # 创建野怪区域标签页
        self.areas_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.areas_frame, text="野怪区域")
        # 创建自动抓捕标签页
        self.farm_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.farm_frame, text="自动抓捕")
        # 创建自动刷野标签页
        self.fight_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.fight_frame, text="自动刷野")

        # 初始化变量
        self.monster_name = ""
        self.config = {}
        self.rgb_points = []
        self.monster_spots = []
        self.levels = []
        self.monitoring = False
        self.fighting = False
        self.running = True
        self.hp_region = None
        self.level_region = None

        # 自动刷野配置
        self.fight_config = {
            "username": "渲染离别",
            "enable_materials": True,
            "medicine_threshold": 25,
            "battle_count": 0,
            "skill_selection": "3",  # 默认选择技能3
            "full_level": False     # 默认精灵未满级
        }

        # 初始化界面
        self.setup_config_tab()
        self.setup_areas_tab()
        self.setup_farm_tab()
        self.setup_fight_tab()

        # 加载默认配置
        self.load_default_config()
        self.load_fight_config()

    def log_message(self, message):
        """记录日志消息到结果框"""
        self.update_result(message)

    def send_wechat_alarm(self, content):
        """发送微信告警"""
        url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=f53de057-28b2-4e43-be2e-481f78605ad6"
        headers = {"Content-Type": "application/json"}
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            self.log(f"[企业微信] 已发送通知：{content}")
        except Exception as e:
            self.log(f"[企业微信] 发送失败：{e}")

    def setup_config_tab(self):
        """设置配置管理标签页"""
        # 野怪配置部分
        monster_frame = ttk.LabelFrame(self.config_frame, text="野怪配置")
        monster_frame.pack(fill=tk.X, padx=10, pady=10)

        # 野怪名称输入
        name_frame = ttk.Frame(monster_frame)
        name_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(name_frame, text="野怪名称:").pack(side=tk.LEFT, padx=5)
        self.monster_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.monster_var, width=20)
        name_entry.pack(side=tk.LEFT, padx=5)

        # 配置操作按钮
        btn_frame = ttk.Frame(name_frame)
        btn_frame.pack(side=tk.RIGHT, padx=5)

        load_btn = ttk.Button(btn_frame, text="加载配置", command=self.load_config)
        load_btn.pack(side=tk.LEFT, padx=2)

        save_btn = ttk.Button(btn_frame, text="保存配置", command=self.save_config)
        save_btn.pack(side=tk.LEFT, padx=2)

        # 等级与血量配置部分
        level_frame = ttk.LabelFrame(self.config_frame, text="等级与血量配置")
        level_frame.pack(fill=tk.X, padx=10, pady=10)

        # 等级1配置
        level1_frame = ttk.Frame(level_frame)
        level1_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(level1_frame, text="等级1:").pack(side=tk.LEFT, padx=5)
        self.level1_var = tk.IntVar()
        level1_entry = ttk.Entry(level1_frame, textvariable=self.level1_var, width=5)
        level1_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(level1_frame, text="血量:").pack(side=tk.LEFT, padx=5)
        self.hp1_var = tk.IntVar()
        hp1_entry = ttk.Entry(level1_frame, textvariable=self.hp1_var, width=5)
        hp1_entry.pack(side=tk.LEFT, padx=5)

        # 等级2配置
        level2_frame = ttk.Frame(level_frame)
        level2_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(level2_frame, text="等级2:").pack(side=tk.LEFT, padx=5)
        self.level2_var = tk.IntVar()
        level2_entry = ttk.Entry(level2_frame, textvariable=self.level2_var, width=5)
        level2_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(level2_frame, text="血量:").pack(side=tk.LEFT, padx=5)
        self.hp2_var = tk.IntVar()
        hp2_entry = ttk.Entry(level2_frame, textvariable=self.hp2_var, width=5)
        hp2_entry.pack(side=tk.LEFT, padx=5)

        # RGB选点配置部分
        rgb_frame = ttk.LabelFrame(self.config_frame, text="RGB选点配置")
        rgb_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 控制面板
        control_frame = ttk.Frame(rgb_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        add_btn = ttk.Button(control_frame, text="添加选点", command=self.add_rgb_point)
        add_btn.pack(side=tk.LEFT, padx=5)

        del_btn = ttk.Button(control_frame, text="删除选点", command=self.delete_rgb_point)
        del_btn.pack(side=tk.LEFT, padx=5)

        test_btn = ttk.Button(control_frame, text="测试选点", command=self.test_rgb_points)
        test_btn.pack(side=tk.LEFT, padx=5)

        # 点列表框架
        list_frame = ttk.Frame(rgb_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建表格
        columns = ("id", "name", "x", "y", "r", "g", "b", "tolerance")
        self.point_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # 设置列标题
        self.point_tree.heading("id", text="ID")
        self.point_tree.heading("name", text="名称")
        self.point_tree.heading("x", text="X坐标")
        self.point_tree.heading("y", text="Y坐标")
        self.point_tree.heading("r", text="R值")
        self.point_tree.heading("g", text="G值")
        self.point_tree.heading("b", text="B值")
        self.point_tree.heading("tolerance", text="容差")

        # 设置列宽
        self.point_tree.column("id", width=40, anchor=tk.CENTER)
        self.point_tree.column("name", width=100, anchor=tk.CENTER)
        self.point_tree.column("x", width=80, anchor=tk.CENTER)
        self.point_tree.column("y", width=80, anchor=tk.CENTER)
        self.point_tree.column("r", width=60, anchor=tk.CENTER)
        self.point_tree.column("g", width=60, anchor=tk.CENTER)
        self.point_tree.column("b", width=60, anchor=tk.CENTER)
        self.point_tree.column("tolerance", width=60, anchor=tk.CENTER)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.point_tree.yview)
        self.point_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.point_tree.pack(fill=tk.BOTH, expand=True)

        # 绑定双击事件
        self.point_tree.bind("<Double-1>", self.edit_rgb_point)

        # 点预览区域
        preview_frame = ttk.LabelFrame(rgb_frame, text="点预览")
        preview_frame.pack(fill=tk.X, padx=5, pady=5)

        self.preview_label = ttk.Label(preview_frame, text="选择一个点查看预览")
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 绑定选择事件
        self.point_tree.bind("<<TreeviewSelect>>", self.show_rgb_preview)

    def setup_areas_tab(self):
        """设置野怪区域标签页"""
        # 控制面板
        control_frame = ttk.Frame(self.areas_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        add_btn = ttk.Button(control_frame, text="添加区域", command=self.add_monster_area)
        add_btn.pack(side=tk.LEFT, padx=5)

        del_btn = ttk.Button(control_frame, text="删除区域", command=self.delete_monster_area)
        del_btn.pack(side=tk.LEFT, padx=5)

        # 区域列表框架
        list_frame = ttk.LabelFrame(self.areas_frame, text="野怪区域列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建表格
        columns = ("id", "label", "x", "y", "width", "height", "image_path")
        self.area_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # 设置列标题
        self.area_tree.heading("id", text="ID")
        self.area_tree.heading("label", text="标签")
        self.area_tree.heading("x", text="X坐标")
        self.area_tree.heading("y", text="Y坐标")
        self.area_tree.heading("width", text="宽度")
        self.area_tree.heading("height", text="高度")
        self.area_tree.heading("image_path", text="图片路径")

        # 设置列宽
        self.area_tree.column("id", width=40, anchor=tk.CENTER)
        self.area_tree.column("label", width=100, anchor=tk.CENTER)
        self.area_tree.column("x", width=60, anchor=tk.CENTER)
        self.area_tree.column("y", width=60, anchor=tk.CENTER)
        self.area_tree.column("width", width=60, anchor=tk.CENTER)
        self.area_tree.column("height", width=60, anchor=tk.CENTER)
        self.area_tree.column("image_path", width=300, anchor=tk.CENTER)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.area_tree.yview)
        self.area_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.area_tree.pack(fill=tk.BOTH, expand=True)

        # 绑定双击事件
        self.area_tree.bind("<Double-1>", self.edit_monster_area)

        # 区域预览区域
        preview_frame = ttk.LabelFrame(self.areas_frame, text="区域预览")
        preview_frame.pack(fill=tk.X, padx=10, pady=10)

        self.area_preview_label = ttk.Label(preview_frame, text="选择一个区域查看预览")
        self.area_preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 绑定选择事件
        self.area_tree.bind("<<TreeviewSelect>>", self.show_area_preview)

    def setup_farm_tab(self):
        """设置自动抓捕标签页"""
        # OCR区域选择部分
        ocr_frame = ttk.LabelFrame(self.farm_frame, text="OCR区域选择")
        ocr_frame.pack(fill=tk.X, padx=10, pady=10)

        # 控制按钮
        btn_frame = ttk.Frame(ocr_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        self.hp_btn = ttk.Button(btn_frame, text="选择血量区域", command=lambda: self.select_area("hp"))
        self.hp_btn.pack(side=tk.LEFT, padx=5)

        self.level_btn = ttk.Button(btn_frame, text="选择等级区域", command=lambda: self.select_area("level"))
        self.level_btn.pack(side=tk.LEFT, padx=5)

        self.monitor_btn = ttk.Button(btn_frame, text="开始监控", command=self.toggle_monitoring)
        self.monitor_btn.pack(side=tk.RIGHT, padx=5)

        # 预览区域
        preview_frame = ttk.Frame(ocr_frame)
        preview_frame.pack(fill=tk.X, padx=5, pady=5)

        # 血量区域预览
        hp_preview_frame = ttk.LabelFrame(preview_frame, text="血量区域")
        hp_preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.hp_preview_label = ttk.Label(hp_preview_frame, text="未选择区域")
        self.hp_preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 等级区域预览
        level_preview_frame = ttk.LabelFrame(preview_frame, text="等级区域")
        level_preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        self.level_preview_label = ttk.Label(level_preview_frame, text="未选择区域")
        self.level_preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 结果输出框
        result_frame = ttk.LabelFrame(self.farm_frame, text="识别结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            height=10,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg='#E4D2E4',
            fg='#000000',
            font=('Consolas', 10)
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def setup_fight_tab(self):
        """设置自动刷野标签页"""
        # 配置部分
        config_frame = ttk.LabelFrame(self.fight_frame, text="刷野配置")
        config_frame.pack(fill=tk.X, padx=10, pady=10)

        # 操作用户
        user_frame = ttk.Frame(config_frame)
        user_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(user_frame, text="操作用户:").pack(side=tk.LEFT, padx=5)
        self.username_var = tk.StringVar(value=self.fight_config["username"])
        user_entry = ttk.Entry(user_frame, textvariable=self.username_var, width=20)
        user_entry.pack(side=tk.LEFT, padx=5)

        # 物资掉落开关
        materials_frame = ttk.Frame(config_frame)
        materials_frame.pack(fill=tk.X, padx=5, pady=5)

        self.materials_var = tk.BooleanVar(value=self.fight_config["enable_materials"])
        materials_cb = ttk.Checkbutton(materials_frame, text="启用物资掉落确认", variable=self.materials_var)
        materials_cb.pack(side=tk.LEFT, padx=5)

        # 刷野精灵是否满级
        full_level_frame = ttk.Frame(config_frame)
        full_level_frame.pack(fill=tk.X, padx=5, pady=5)

        self.full_level_var = tk.BooleanVar(value=self.fight_config["full_level"])
        full_level_cb = ttk.Checkbutton(full_level_frame, text="刷野精灵是否满级", variable=self.full_level_var)
        full_level_cb.pack(side=tk.LEFT, padx=5)

        # 技能选择
        skill_frame = ttk.Frame(config_frame)
        skill_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(skill_frame, text="技能选择:").pack(side=tk.LEFT, padx=5)
        self.skill_var = tk.StringVar(value=self.fight_config["skill_selection"])
        skill_combo = ttk.Combobox(skill_frame, textvariable=self.skill_var, width=5, state="readonly")
        skill_combo['values'] = ("2", "3", "4")
        skill_combo.pack(side=tk.LEFT, padx=5)

        # 吃药循环次数
        medicine_frame = ttk.Frame(config_frame)
        medicine_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(medicine_frame, text="吃药循环次数:").pack(side=tk.LEFT, padx=5)
        self.medicine_var = tk.IntVar(value=self.fight_config["medicine_threshold"])
        medicine_entry = ttk.Entry(medicine_frame, textvariable=self.medicine_var, width=10)
        medicine_entry.pack(side=tk.LEFT, padx=5)

        # 保存配置按钮
        btn_frame = ttk.Frame(config_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        save_btn = ttk.Button(btn_frame, text="保存配置", command=self.save_fight_config)
        save_btn.pack(side=tk.RIGHT, padx=5)

        # 刷野控制
        control_frame = ttk.LabelFrame(self.fight_frame, text="刷野控制")
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        self.fight_btn = ttk.Button(control_frame, text="开始刷野", command=self.toggle_fighting)
        self.fight_btn.pack(pady=10)

        # 刷野状态
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.battle_count_var = tk.StringVar(value=f"当前战斗次数: {self.fight_config['battle_count']}")
        self.battle_label = ttk.Label(status_frame, textvariable=self.battle_count_var)
        self.battle_label.pack()

        # 结果输出框
        result_frame = ttk.LabelFrame(self.fight_frame, text="刷野日志")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.fight_text = scrolledtext.ScrolledText(
            result_frame,
            height=10,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg='#E4D2E4',
            fg='#000000',
            font=('Consolas', 10)
        )
        self.fight_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def load_default_config(self):
        """加载默认配置（如果有）"""
        try:
            # 尝试加载最近使用的配置
            if os.path.exists("config/last_config.json"):
                with open("config/last_config.json", "r") as f:
                    last_config = json.load(f)
                    self.monster_var.set(last_config.get("monster_name", ""))
                    self.load_config()
        except:
            pass
    
    def load_fight_config(self):
        """加载刷野配置"""
        config_path = os.path.join("config", "fight_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    self.fight_config = json.load(f)
                # 更新界面
                self.username_var.set(self.fight_config["username"])
                self.materials_var.set(self.fight_config["enable_materials"])
                self.medicine_var.set(self.fight_config["medicine_threshold"])
                self.battle_count_var.set(f"当前战斗次数: {self.fight_config['battle_count']}")
                self.skill_var.set(self.fight_config.get("skill_selection", "3"))
                self.full_level_var.set(self.fight_config.get("full_level", False))
                self.update_fight_log(f"加载刷野配置成功")
            except Exception as e:
                self.update_fight_log(f"加载刷野配置失败: {e}")
        else:
            self.update_fight_log("未找到刷野配置，使用默认配置")
    
    def save_fight_config(self):
        """保存刷野配置"""
        self.fight_config = {
            "username": self.username_var.get(),
            "enable_materials": self.materials_var.get(),
            "medicine_threshold": self.medicine_var.get(),
            "battle_count": self.fight_config.get("battle_count", 0),
            "skill_selection": self.skill_var.get(),
            "full_level": self.full_level_var.get()
        }
        
        config_path = os.path.join("config", "fight_config.json")
        try:
            with open(config_path, "w") as f:
                json.dump(self.fight_config, f, indent=4)
            self.update_fight_log(f"刷野配置已保存到 {config_path}")
        except Exception as e:
            self.update_fight_log(f"保存刷野配置失败: {e}")
    
    def load_config(self):
        """加载配置"""
        self.monster_name = self.monster_var.get().strip()
        if not self.monster_name:
            messagebox.showwarning("警告", "请输入野怪名称")
            return
        
        config_path = os.path.join("config", f"{self.monster_name}_config.json")
        if not os.path.exists(config_path):
            messagebox.showinfo("信息", f"未找到 {self.monster_name} 的配置文件")
            return
        
        try:
            with open(config_path, "r") as f:
                self.config = json.load(f)
            
            # 更新野怪名称
            self.monster_var.set(self.monster_name)
            
            # 更新等级与血量配置
            if "levels" in self.config and len(self.config["levels"]) >= 2:
                self.level1_var.set(self.config["levels"][0]["level"])
                self.hp1_var.set(self.config["levels"][0]["max_hp"])
                self.level2_var.set(self.config["levels"][1]["level"])
                self.hp2_var.set(self.config["levels"][1]["max_hp"])
            
            # 更新RGB选点配置
            self.rgb_points = self.config.get("rgb_points", [])
            self.update_point_tree()
            
            # 更新野怪区域配置
            self.monster_spots = self.config.get("monster_spots", [])
            self.update_area_tree()
            
            # 保存为最近使用的配置
            with open("config/last_config.json", "w") as f:
                json.dump({"monster_name": self.monster_name}, f, indent=4)
            
            self.log_message(f"成功加载 {self.monster_name} 配置")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {e}")
            self.log_message(f"加载配置失败: {e}")
    
    def save_config(self):
        """保存配置"""
        self.monster_name = self.monster_var.get().strip()
        if not self.monster_name:
            messagebox.showwarning("警告", "请输入野怪名称")
            return
        
        # 验证等级与血量配置
        try:
            level1 = self.level1_var.get()
            hp1 = self.hp1_var.get()
            level2 = self.level2_var.get()
            hp2 = self.hp2_var.get()
            
            if level1 <= 0 or hp1 <= 0 or level2 <= 0 or hp2 <= 0:
                raise ValueError("等级和血量必须大于0")
        except Exception as e:
            messagebox.showerror("错误", f"无效的等级或血量配置: {e}")
            return
        
        # 构建配置对象
        self.config = {
            "monster_name": self.monster_name,
            "levels": [
                {"level": level1, "max_hp": hp1},
                {"level": level2, "max_hp": hp2}
            ],
            "rgb_points": self.rgb_points,
            "monster_spots": self.monster_spots
        }
        
        # 保存到文件
        config_path = os.path.join("config", f"{self.monster_name}_config.json")
        try:
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=4)
            
            # 保存为最近使用的配置
            with open("config/last_config.json", "w") as f:
                json.dump({"monster_name": self.monster_name}, f, indent=4)
            
            messagebox.showinfo("成功", f"配置已保存到 {config_path}")
            self.log_message(f"配置已保存到 {config_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
            self.log_message(f"保存配置失败: {e}")
    
    def add_rgb_point(self):
        """添加新的RGB点"""
        # 在正常亮度下快速截取全屏
        self.full_screenshot = ImageGrab.grab()
        
        # 创建全屏透明窗口用于选择位置
        self.root.withdraw()
        
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.3)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.config(bg='black')
        
        # 创建画布用于绘制选择框
        self.canvas = tk.Canvas(self.selection_window, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 添加提示文字
        self.canvas.create_text(
            self.selection_window.winfo_screenwidth() // 2,
            50,
            text="点击屏幕选择点位",
            fill="white",
            font=("Arial", 24, "bold")
        )
        
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_rgb_press)
        self.selection_window.bind("<Escape>", self.cancel_rgb_selection)
    
    def on_rgb_press(self, event):
        """处理鼠标点击事件 - 使用正常亮度截图获取RGB值"""
        x, y = event.x, event.y
        
        # 从正常亮度截图中获取该点的RGB值
        if hasattr(self, 'full_screenshot') and self.full_screenshot:
            try:
                rgb = self.full_screenshot.getpixel((x, y))
            except:
                # 如果坐标超出范围，使用默认值
                rgb = (0, 0, 0)
        else:
            # 如果没有截图，尝试实时获取
            screenshot = ImageGrab.grab()
            rgb = screenshot.getpixel((x, y))
        
        # 创建点信息
        point_id = len(self.rgb_points) + 1
        point = {
            "id": point_id,
            "name": f"点位{point_id}",
            "x": x,
            "y": y,
            "r": rgb[0],
            "g": rgb[1],
            "b": rgb[2],
            "tolerance": 0  # 默认容差
        }
        
        # 添加到点列表
        self.rgb_points.append(point)
        
        # 更新树形视图
        self.update_point_tree()
        
        # 关闭选择窗口
        self.selection_window.destroy()
        self.root.deiconify()
        
        # 清除全屏截图以释放内存
        if hasattr(self, 'full_screenshot'):
            del self.full_screenshot
        
        # 弹出编辑窗口
        self.edit_rgb_point_dialog(point)
    
    def edit_rgb_point_dialog(self, point):
        """编辑点信息对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑点位信息")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 名称输入
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(name_frame, text="点位名称:").pack(side=tk.LEFT)
        name_var = tk.StringVar(value=point["name"])
        name_entry = ttk.Entry(name_frame, textvariable=name_var)
        name_entry.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)
        
        # 坐标显示
        coord_frame = ttk.Frame(dialog)
        coord_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(coord_frame, text=f"坐标: ({point['x']}, {point['y']})").pack()
        
        # RGB显示
        rgb_frame = ttk.Frame(dialog)
        rgb_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(rgb_frame, text=f"预设RGB值: ({point['r']}, {point['g']}, {point['b']})").pack()
        
        # 颜色预览
        color_canvas = tk.Canvas(dialog, width=100, height=30, bg=self.rgb_to_hex(point))
        color_canvas.pack(pady=10)
        
        # 容差设置
        tol_frame = ttk.Frame(dialog)
        tol_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(tol_frame, text="容差值:").pack(side=tk.LEFT)
        tol_var = tk.IntVar(value=point["tolerance"])
        tol_scale = ttk.Scale(tol_frame, from_=1, to=50, variable=tol_var, orient=tk.HORIZONTAL)
        tol_scale.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tol_label = ttk.Label(tol_frame, textvariable=tk.StringVar(value=str(tol_var.get())))
        tol_label.pack(side=tk.LEFT, padx=5)
        
        # 更新容差值显示
        def update_tol_label(*args):
            tol_label.config(text=str(tol_var.get()))
        
        tol_var.trace_add("write", update_tol_label)
        
        # 保存按钮
        def save_point():
            point["name"] = name_var.get()
            point["tolerance"] = tol_var.get()
            self.update_point_tree()
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="保存", command=save_point).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def edit_rgb_point(self, event):
        """编辑选中的点"""
        selected = self.point_tree.selection()
        if not selected:
            return
            
        item = self.point_tree.item(selected[0])
        point_id = item["values"][0]
        
        # 查找对应的点
        for point in self.rgb_points:
            if point["id"] == point_id:
                self.edit_rgb_point_dialog(point)
                break
    
    def delete_rgb_point(self):
        """删除选中的点"""
        selected = self.point_tree.selection()
        if not selected:
            return
            
        item = self.point_tree.item(selected[0])
        point_id = item["values"][0]
        
        # 从点列表中删除
        self.rgb_points = [p for p in self.rgb_points if p["id"] != point_id]
        
        # 重新生成ID
        for i, point in enumerate(self.rgb_points):
            point["id"] = i + 1
        
        # 更新树形视图
        self.update_point_tree()
        self.log_message(f"已删除RGB点 ID:{point_id}")
    
    def update_point_tree(self):
        """更新点列表树形视图"""
        # 清空树形视图
        for item in self.point_tree.get_children():
            self.point_tree.delete(item)
        
        # 添加点数据
        for point in self.rgb_points:
            self.point_tree.insert("", "end", values=(
                point["id"],
                point["name"],
                point["x"],
                point["y"],
                point["r"],
                point["g"],
                point["b"],
                point["tolerance"]
            ))
    
    def show_rgb_preview(self, event):
        """显示点预览"""
        selected = self.point_tree.selection()
        if not selected:
            return
            
        item = self.point_tree.item(selected[0])
        values = item["values"]
        x, y = values[2], values[3]
        
        # 截取点周围的区域
        region_size = 50
        bbox = (x - region_size//2, y - region_size//2, 
                x + region_size//2, y + region_size//2)
        
        try:
            # 截取屏幕
            screenshot = ImageGrab.grab(bbox=bbox)
            
            # 绘制标记
            img = screenshot.copy()
            draw = Image.new('RGBA', img.size, (0, 0, 0, 0))
            center = (region_size//2, region_size//2)
            
            # 创建绘图上下文
            draw_img = ImageDraw.Draw(draw)
            
            # 绘制十字线
            draw_img.line([(center[0]-10, center[1]), (center[0]+10, center[1])], 
                         fill="red", width=2)
            draw_img.line([(center[0], center[1]-10), (center[0], center[1]+10)], 
                         fill="red", width=2)
            
            # 绘制圆环
            draw_img.ellipse([(center[0]-5, center[1]-5), (center[0]+5, center[1]+5)], 
                            outline="red", width=2)
            
            # 合并图像
            img = Image.alpha_composite(img.convert('RGBA'), draw)
            img = img.convert('RGB')
            
            # 调整大小
            img = img.resize((200, 200), Image.LANCZOS)
            
            # 显示图像
            photo = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo
        except Exception as e:
            print(f"预览错误: {e}")
    
    def rgb_to_hex(self, point):
        """将RGB值转换为十六进制颜色代码"""
        return f"#{point['r']:02x}{point['g']:02x}{point['b']:02x}"
    
    def test_rgb_points(self):
        """测试RGB点匹配"""
        if not self.rgb_points:
            messagebox.showwarning("警告", "请先添加至少一个测试点")
            return
        
        # 测试所有点
        all_matched = True
        results = []
        
        for point in self.rgb_points:
            # 获取当前点的RGB值
            screenshot = ImageGrab.grab()
            try:
                current_rgb = screenshot.getpixel((point["x"], point["y"]))
            except Exception as e:
                print(f"获取点({point['x']}, {point['y']})颜色失败: {e}")
                current_rgb = (0, 0, 0)
            
            # 计算颜色差异
            diff_r = abs(current_rgb[0] - point["r"])
            diff_g = abs(current_rgb[1] - point["g"])
            diff_b = abs(current_rgb[2] - point["b"])
            
            # 检查是否匹配
            tolerance = point["tolerance"]
            matched = diff_r <= tolerance and diff_g <= tolerance and diff_b <= tolerance
            
            # 更新整体匹配状态
            if not matched:
                all_matched = False
            
            # 记录结果
            results.append({
                "point": point,
                "current_rgb": current_rgb,
                "matched": matched
            })
        
        # 显示结果
        result_text = "RGB点测试结果:\n"
        for result in results:
            point = result["point"]
            current_rgb = result["current_rgb"]
            matched = result["matched"]
            
            status = "匹配" if matched else "不匹配"
            result_text += (
                f"点 {point['name']} ({point['x']}, {point['y']}): "
                f"预设({point['r']},{point['g']},{point['b']}) "
                f"实际({current_rgb[0]},{current_rgb[1]},{current_rgb[2]}) - {status}\n"
            )
        
        result_text += f"\n整体状态: {'全部匹配' if all_matched else '部分不匹配'}"
        
        # 在结果框中显示
        self.update_result(result_text)
        
        # 在日志中记录
        self.log_message(f"RGB点测试: {'全部匹配' if all_matched else '部分不匹配'}")
    
    def add_monster_area(self):
        """添加野怪区域"""
        # 创建全屏透明窗口用于选择区域
        self.root.withdraw()
        
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.3)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.config(bg='black')
        
        # 创建画布用于绘制选择框
        self.canvas = tk.Canvas(self.selection_window, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 添加提示文字
        self.canvas.create_text(
            self.selection_window.winfo_screenwidth() // 2,
            50,
            text="拖动鼠标选择野怪区域(单击取消)",
            fill="white",
            font=("Arial", 24, "bold")
        )
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_monster_press)
        self.canvas.bind("<B1-Motion>", self.on_monster_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_monster_release)
        self.selection_window.bind("<Escape>", self.cancel_monster_selection)
    
    def on_monster_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        
    def on_monster_drag(self, event):
        if self.rect:
            self.canvas.delete(self.rect)
            
        x, y = (event.x, event.y)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, x, y, 
            outline='red', width=2, dash=(4, 4)
        )
        
    def on_monster_release(self, event):
        end_x, end_y = (event.x, event.y)
        
        # 确保坐标是左上角和右下角
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        # 保存选择的区域
        region = (x1, y1, x2 - x1, y2 - y1)
        
        # 关闭选择窗口
        self.selection_window.destroy()
        self.root.deiconify()
        
        # 保存截图
        monster_dir = os.path.join("images", self.monster_name)
        os.makedirs(monster_dir, exist_ok=True)
        
        # 使用时间戳确保文件名唯一
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"monster_spot_{timestamp}.png"
        image_path = os.path.join(monster_dir, filename)
        
        # 截取区域并保存
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(image_path)
        
        # 创建区域信息
        area_id = len(self.monster_spots) + 1
        self.monster_spots.append({
            "id": area_id,
            "region": region,
            "image_path": image_path,
            "label": f"区域{area_id}",
            "click_coord": (region[0] + region[2]//2, region[1] + region[3]//2)
        })
        
        # 更新区域树
        self.update_area_tree()
        self.log_message(f"添加野怪区域 ID:{area_id}")
    
    def delete_monster_area(self):
        """删除野怪区域"""
        selected = self.area_tree.selection()
        if not selected:
            return
            
        item = self.area_tree.item(selected[0])
        area_id = item["values"][0]
        
        # 删除图片功能
        area_to_delete = next((a for a in self.monster_spots if a["id"] == area_id), None)
        if area_to_delete and os.path.exists(area_to_delete["image_path"]):
            try:
                os.remove(area_to_delete["image_path"])
                self.log_message(f"已删除区域图片: {area_to_delete['image_path']}")
            except Exception as e:
                self.log_message(f"删除图片失败: {e}")

        # 从区域列表中删除
        self.monster_spots = [a for a in self.monster_spots if a["id"] != area_id]
        
        # 重新生成ID
        for i, area in enumerate(self.monster_spots):
            area["id"] = i + 1
        
        # 更新树形视图
        self.update_area_tree()
        self.log_message(f"已删除野怪区域 ID:{area_id}")
    
    def edit_monster_area(self, event):
        """编辑野怪区域（暂不实现）"""
        messagebox.showinfo("信息", "编辑功能暂未实现，请删除后重新添加")
    
    def update_area_tree(self):
        """更新区域列表树形视图"""
        # 清空树形视图
        for item in self.area_tree.get_children():
            self.area_tree.delete(item)
        
        # 添加区域数据
        for area in self.monster_spots:
            region = area["region"]
            self.area_tree.insert("", "end", values=(
                area["id"],
                area["label"],
                region[0],
                region[1],
                region[2],
                region[3],
                area["image_path"]
            ))
    
    def show_area_preview(self, event):
        """显示区域预览 - 在白色背景上显示所有区域贴图"""
        # 获取当前选中的区域ID
        selected_id = None
        selected = self.area_tree.selection()
        if selected:
            item = self.area_tree.item(selected[0])
            values = item["values"]
            selected_id = values[0]  # 区域ID
        
        # 获取当前屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 创建预览图像（使用实际屏幕尺寸的1/4大小）
        preview_width = screen_width // 2
        preview_height = screen_height // 2
        scale_factor = preview_width / screen_width
        
        # 创建白色背景图像
        bg_color = (255, 255, 255)  # 白色背景
        preview_img = Image.new('RGB', (preview_width, preview_height), bg_color)
        draw = ImageDraw.Draw(preview_img)
        
        # 绘制所有区域
        for area in self.monster_spots:
            # 计算缩放后的坐标和尺寸
            x, y, width, height = area["region"]
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            scaled_width = int(width * scale_factor)
            scaled_height = int(height * scale_factor)
            
            # 加载区域图像
            try:
                area_img = Image.open(area["image_path"])
                # 调整图像大小
                area_img = area_img.resize((scaled_width, scaled_height), Image.LANCZOS)
                # 将区域图像粘贴到预览背景上
                preview_img.paste(area_img, (scaled_x, scaled_y))
            except Exception as e:
                print(f"加载区域图像错误: {e}")
            
            # 如果是当前选中的区域，添加红色边框
            if selected_id is not None and area["id"] == selected_id:
                # 绘制红色边框
                draw.rectangle(
                    [scaled_x, scaled_y, scaled_x + scaled_width, scaled_y + scaled_height],
                    outline="red", 
                    width=3
                )
       
        # 创建可点击的预览标签
        photo = ImageTk.PhotoImage(preview_img)
        self.area_preview_label.configure(image=photo)
        self.area_preview_label.image = photo
        
        # 绑定点击事件以放大预览
        self.area_preview_label.bind("<Button-1>", lambda e: self.show_full_preview(preview_img))

    def show_full_preview(self, preview_img):
        """显示完整大小的预览图"""
        # 创建新窗口显示完整预览
        preview_window = tk.Toplevel(self.root)
        preview_window.title("完整区域预览")
        preview_window.geometry(f"{preview_img.width}x{preview_img.height}")
        
        # 创建图像标签
        photo = ImageTk.PhotoImage(preview_img)
        preview_label = tk.Label(preview_window, image=photo)
        preview_label.image = photo  # 保持引用
        preview_label.pack(fill=tk.BOTH, expand=True)
        
        # 添加关闭按钮
        close_btn = ttk.Button(preview_window, text="关闭", command=preview_window.destroy)
        close_btn.pack(pady=10)
    
    def select_area(self, area_type):
        """选择OCR区域"""
        if self.monitoring:
            messagebox.showwarning("警告", "请先停止监控再修改区域")
            return
            
        # 创建全屏透明窗口用于选择区域
        self.root.withdraw()
        
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.3)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.config(bg='black')
        
        # 创建画布用于绘制选择框
        self.canvas = tk.Canvas(self.selection_window, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 添加提示文字
        self.canvas.create_text(
            self.selection_window.winfo_screenwidth() // 2,
            50,
            text=f"拖动鼠标选择{area_type}区域 (ESC取消)",
            fill="white",
            font=("Arial", 24, "bold")
        )
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.area_type = area_type
        
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_area_press)
        self.canvas.bind("<B1-Motion>", self.on_area_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_area_release)
        self.selection_window.bind("<Escape>", self.cancel_area_selection)
    
    def on_area_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        
    def on_area_drag(self, event):
        if self.rect:
            self.canvas.delete(self.rect)
            
        x, y = (event.x, event.y)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, x, y, 
            outline='red', width=2, dash=(4, 4)
        )
        
    def on_area_release(self, event):
        end_x, end_y = (event.x, event.y)
        
        # 确保坐标是左上角和右下角
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        # 保存选择的区域
        region = (x1, y1, x2 - x1, y2 - y1)
        
        # 关闭选择窗口
        self.selection_window.destroy()
        self.root.deiconify()
        
        # 更新预览
        if self.area_type == "hp":
            self.hp_region = region
            self.update_ocr_preview(self.hp_preview_label, region, "血量区域")
            self.log_message(f"已选择血量区域: ({x1}, {y1}) - ({x2}, {y2})")
        else:
            self.level_region = region
            self.update_ocr_preview(self.level_preview_label, region, "等级区域")
            self.log_message(f"已选择等级区域: ({x1}, {y1}) - ({x2}, {y2})")
    
    def update_ocr_preview(self, label_widget, region, title):
        if not region:
            return
            
        # 截取选择的区域
        x1, y1, width, height = region
        if width <= 0 or height <= 0:
            return
        
        # 截取屏幕
        screenshot = ImageGrab.grab(bbox=(x1, y1, x1 + width, y1 + height))
        
        # 调整大小以适应预览
        max_size = 200
        ratio = min(max_size / width, max_size / height)
        new_size = (int(width * ratio), int(height * ratio))
        resized_img = screenshot.resize(new_size, Image.LANCZOS)
        
        # 显示截图预览
        photo = ImageTk.PhotoImage(resized_img)
        label_widget.configure(image=photo)
        label_widget.image = photo
    
    def cancel_rgb_selection(self, event=None):
        """取消RGB点选择"""
        self.selection_window.destroy()
        self.root.deiconify()
    
    def cancel_area_selection(self, event=None):
        """取消区域选择"""
        self.selection_window.destroy()
        self.root.deiconify()
    
    def cancel_monster_selection(self, event=None):
        """取消野怪区域选择"""
        self.selection_window.destroy()
        self.root.deiconify()
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.hp_region or not self.level_region:
            messagebox.showwarning("警告", "请先选择血量和等级区域")
            return
            
        if not self.monster_spots:
            messagebox.showwarning("警告", "请配置至少一个野怪区域")
            return
            
        if not self.rgb_points:
            messagebox.showwarning("警告", "请配置至少一个RGB点")
            return
            
        # 检查等级与血量配置是否已设置
        try:
            level1 = self.level1_var.get()
            hp1 = self.hp1_var.get()
            level2 = self.level2_var.get()
            hp2 = self.hp2_var.get()
            
            if level1 <= 0 or hp1 <= 0 or level2 <= 0 or hp2 <= 0:
                raise ValueError("等级和血量必须大于0")
        except Exception as e:
            messagebox.showwarning("警告", f"请配置有效的等级和血量信息: {e}")
            return
            
        self.monitoring = not self.monitoring
        if self.monitoring:
            self.monitor_btn.config(text="停止监控")
            self.log_message("开始监控...")
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self.monitoring_task, daemon=True)
            self.monitor_thread.start()
        else:
            self.monitor_btn.config(text="开始监控")
            self.log_message("监控已停止")
    
    def toggle_fighting(self):
        """切换刷野状态"""
        if not self.monster_spots:
            messagebox.showwarning("警告", "请配置至少一个野怪区域")
            return
            
        if not self.rgb_points:
            messagebox.showwarning("警告", "请配置至少一个RGB点")
            return
            
        self.fighting = not self.fighting
        if self.fighting:
            self.fight_btn.config(text="停止刷野")
            self.update_fight_log("开始刷野...")
            # 启动刷野线程
            self.fight_thread = threading.Thread(target=self.fighting_task, daemon=True)
            self.fight_thread.start()
        else:
            self.fight_btn.config(text="开始刷野")
            self.update_fight_log("刷野已停止")
    
    def check_rgb_points(self):
        """检查所有RGB点是否匹配"""
        if not self.rgb_points:
            return False
        
        all_matched = True
        
        for point in self.rgb_points:
            # 获取当前点的RGB值
            screenshot = ImageGrab.grab()
            try:
                current_rgb = screenshot.getpixel((point["x"], point["y"]))
            except:
                current_rgb = (0, 0, 0)
            
            # 计算颜色差异
            diff_r = abs(current_rgb[0] - point["r"])
            diff_g = abs(current_rgb[1] - point["g"])
            diff_b = abs(current_rgb[2] - point["b"])
            
            # 检查是否匹配
            tolerance = point["tolerance"]
            matched = diff_r <= tolerance and diff_g <= tolerance and diff_b <= tolerance
            
            if not matched:
                all_matched = False
                break
        
        return all_matched
    
    def recognize_digits(self, region, preprocess=True):
        """识别指定区域的数字"""
        if not region:
            return None
            
        # 截取屏幕区域
        x1, y1, width, height = region
        screenshot = ImageGrab.grab(bbox=(x1, y1, x1 + width, y1 + height))
        
        # 预处理图像
        if preprocess:
            img = screenshot.convert('L')
            img_np = np.array(img)
            _, img_np = cv2.threshold(img_np, 180, 255, cv2.THRESH_BINARY)
            img = Image.fromarray(img_np)
        else:
            img = screenshot
        
        # 使用Tesseract进行OCR识别
        custom_config = r'--oem 3 --psm 6 outputbase digits'
        try:
            result = pytesseract.image_to_string(img, config=custom_config)
        except Exception as e:
            self.log_message(f"OCR识别错误: {e}")
            return None
        
        # 清理识别结果，只保留数字
        digits = ''.join(filter(str.isdigit, result))
        try:
            return int(digits) if digits else None
        except ValueError:
            return None
    
    def update_result(self, text):
        """更新识别结果文本框"""
        try:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.insert(tk.END, text + "\n")
            self.result_text.see(tk.END)  # 滚动到底部
            self.result_text.config(state=tk.DISABLED)
        except tk.TclError:
            # 窗口可能已经关闭，忽略
            pass
    
    def update_fight_log(self, text):
        """更新刷野日志文本框"""
        try:
            self.fight_text.config(state=tk.NORMAL)
            self.fight_text.insert(tk.END, text + "\n")
            self.fight_text.see(tk.END)  # 滚动到底部
            self.fight_text.config(state=tk.DISABLED)
        except tk.TclError:
            pass
    
    def detect_image(self, region, template_path, confidence_threshold=0.8):
        """检测图像"""
        try:
            screen = pyautogui.screenshot(region=region)
            screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            template = cv2.imread(template_path)
            
            if template is None:
                self.log_message(f"[图像识别] 无法读取模板图像：{template_path}")
                return False, 0, (0, 0)
            
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 计算实际位置（相对于屏幕）
            top_left = max_loc
            actual_x = region[0] + top_left[0] + template.shape[1] // 2
            actual_y = region[1] + top_left[1] + template.shape[0] // 2
            
            return max_val >= confidence_threshold, max_val, (actual_x, actual_y)
        except Exception as e:
            self.log_message(f"[图像识别] 出错：{e}")
            return False, 0, (0, 0)
    
    def execute_click_step(self, coord, label, delay_after=0.5, repeat=1):
        """执行点击操作"""
        for r in range(repeat):
            self.log_message(f"点击：{label} ({coord[0]}, {coord[1]})（{r+1}/{repeat}）")
            pyautogui.moveTo(coord[0], coord[1], duration=0.2)
            pyautogui.click()
            if repeat > 1:
                time.sleep(0.1)  # 多次点击之间短暂间隔
        time.sleep(delay_after)
    
    def execute_click_group(self, click_steps):
        """执行一组点击操作"""
        for step in click_steps:
            self.execute_click_step(
                coord=step["coord"],
                label=step["label"],
                delay_after=step["delay_after"],
                repeat=step["repeat"]
            )
    
    def monitoring_task(self):
        """监控任务"""
        # 逃跑点击组
        escape_clicks = [
            {"coord": (1607, 935), "label": "点击逃跑", "repeat": 1, "delay_after": 0.2},
            {"coord": (843, 673), "label": "逃跑确认", "repeat": 1, "delay_after": 1},
            {"coord": (956, 673), "label": "结束确认", "repeat": 1, "delay_after": 0},
        ]
        
        # 获取等级与血量配置
        level1 = self.level1_var.get()
        hp1 = self.hp1_var.get()
        level2 = self.level2_var.get()
        hp2 = self.hp2_var.get()
        levels = [
            {"level": level1, "max_hp": hp1},
            {"level": level2, "max_hp": hp2}
        ]
        
        # 找出最高等级对应的最高血量
        max_level = max([level["level"] for level in levels])
        max_level_hp = next(level["max_hp"] for level in levels if level["level"] == max_level)
        
        self.log_message(f"\n开始抓捕 {self.monster_name}，最高等级 {max_level} 的最高血量: {max_level_hp}")
        
        while self.monitoring and self.running:
            # 步骤1: 检测野怪点位
            spot_found = False
            for spot in self.monster_spots:
                detected, confidence, _ = self.detect_image(spot["region"], spot["image_path"], 0.7)
                self.log_message(f"检测野怪点位 '{spot['label']}' - 匹配度: {confidence:.4f}")
                
                if detected:
                    self.log_message(f"\n✅ 检测到{spot['label']}，准备攻击... (匹配度: {confidence:.4f})")
                    
                    # 点击野怪点位
                    self.execute_click_step(
                        coord=spot["click_coord"],
                        label=spot["label"],
                        delay_after=0.3,
                        repeat=1
                    )
                    
                    spot_found = True
                    break
            
            if spot_found:
                # 步骤2: 等待战斗开始
                fight_detected = False
                start_time = time.time()
                
                while time.time() - start_time < 5 and self.running and self.monitoring:
                    detected, confidence, _ = self.detect_image(FIGHT_REGION, FIGHT_IMAGE_PATH, 0.8)
                    self.log_message(f"检测战斗界面 - 匹配度: {confidence:.4f}")
                    
                    if detected:
                        self.log_message(f"\n✅ 已进入战斗场景 (匹配度: {confidence:.4f})")
                        fight_detected = True
                        time.sleep(0.5)
                        break
                    time.sleep(0.3)
                
                if not fight_detected:
                    self.log_message("❌ 未检测到战斗场景，重新寻找野怪...")
                    time.sleep(0.5)
                    continue
                
                # 步骤3: 使用RGB点检测普通形态
                is_normal = self.check_rgb_points()
                self.log_message(f"普通形态检测: {'是' if is_normal else '否'}")
                
                # 识别血量和等级
                hp_value = self.recognize_digits(self.hp_region)
                level_value = self.recognize_digits(self.level_region)
                
                result_text = f"识别结果: HP={hp_value if hp_value is not None else 'N/A'}, Level={level_value if level_value is not None else 'N/A'}"
                self.log_message(result_text)
                self.root.after(0, self.update_result, result_text)
                
                # 判断是否为高个体精灵
                high_iv_detected = False
                
                if is_normal and hp_value is not None and level_value is not None:
                    # 情况1: 血量等于最高等级的最高血量
                    if hp_value == max_level_hp:
                        high_iv_detected = True
                        result_text = f"✅ 高个体精灵! (最高等级 {max_level} 最高血量 {max_level_hp})"
                    # 情况2: 血量等于低等级的最高血量且等级匹配
                    elif hp_value in [level["max_hp"] for level in levels]:
                        # 找到血量对应的等级
                        for level_info in levels:
                            if hp_value == level_info["max_hp"] and level_value == level_info["level"]:
                                high_iv_detected = True
                                result_text = f"✅ 高个体精灵! (等级 {level_info['level']} 最高血量 {level_info['max_hp']})"
                                break
                
                # 高个体精灵处理
                if high_iv_detected or not is_normal:
                    self.log_message(result_text)
                    self.root.after(0, self.update_result, result_text)
                    
                    # 发出告警声音
                    self.log_message("发现【特殊】精灵!!!")
                    self.send_wechat_alarm(f"❗ {self.fight_config['username']} ❗ 抓捕过程中发现【特殊】形态精灵，等待人工处理…")
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    
                    # 继续寻找下一个野怪
                    self.log_message("重新扫描野怪区域...")
                    time.sleep(2)
                    continue
                
                # 不是高个体精灵，执行逃跑
                self.log_message("❌ 非高个体精灵，执行逃跑...")
                time.sleep(1.2)
                self.execute_click_group(escape_clicks)
                time.sleep(1)
            else:
                self.log_message("未检测到野怪，继续搜索...")
                time.sleep(0.3)
    
    def fighting_task(self):
        """刷野任务"""
        # 战斗结束后的点击组
        battle_end_clicks = [
            {"coord": (956, 694), "label": "单点确认", "repeat": 1, "delay_after": 0.2},
            {"coord": (974, 767), "label": "升级支持", "repeat": 1, "delay_after": 0.1},
            {"coord": (956, 694), "label": "单点确认", "repeat": 1, "delay_after": 0.2},
            {"coord": (956, 694), "label": "获取经验", "repeat": 1, "delay_after": 0.2},
        ]
        full_level_clicks = [
            {"coord": (956, 694), "label": "单点确认", "repeat": 2, "delay_after": 0.2},
        ]
        # 根据技能选择确定坐标
        skill = self.fight_config.get("skill_selection", "3")
        if skill == "2":
            skill_coord = (1185, 858)
        elif skill == "3":
            skill_coord = (995, 945)
        elif skill == "4":
            skill_coord = (1189, 945)
        else:
            # 默认使用技能3
            skill_coord = (995, 945)
        
        # 战斗步骤
        battle_steps = [
            {"coord": skill_coord, "label": f"释放技能{skill}", "delay_after": 1.5, "repeat": 1}
        ]
        
        # 吃药步骤
        medicine_steps = [
            {"coord": (1547, 975), "label": "精灵背包", "delay_after": 0.3, "repeat": 1},
            {"coord": (894, 796), "label": "恢复精灵", "delay_after": 0.3, "repeat": 1},
            {"coord": (955, 674), "label": "点击确定", "delay_after": 0.3, "repeat": 1},
            {"coord": (904, 331), "label": "点击关闭", "delay_after": 0.3, "repeat": 1},
        ]
        
        self.update_fight_log(f"\n开始刷野 {self.monster_name}，使用技能{skill}")
        
        while self.fighting and self.running:
            # 检查是否需要吃药
            if self.fight_config["battle_count"] >= self.fight_config["medicine_threshold"]:
                self.update_fight_log(f"\n执行【吃药】恢复操作 (战斗次数: {self.fight_config['battle_count']})")
                self.execute_click_group(medicine_steps)
                self.fight_config["battle_count"] = 0
                self.save_fight_config()
                self.battle_count_var.set(f"当前战斗次数: {self.fight_config['battle_count']}")
                self.update_fight_log("✅ 吃药恢复操作【完成】")
                time.sleep(1)
                continue
                
            # 步骤1: 检测野怪点位
            spot_found = False
            for spot in self.monster_spots:
                detected, confidence, _ = self.detect_image(spot["region"], spot["image_path"], 0.7)
                self.update_fight_log(f"检测野怪点位 '{spot['label']}' - 匹配度: {confidence:.4f}")
                
                if detected:
                    self.update_fight_log(f"\n✅ 检测到{spot['label']}，准备【攻击】... (匹配度: {confidence:.4f})")
                    
                    # 点击野怪点位
                    self.execute_click_step(
                        coord=spot["click_coord"],
                        label=spot["label"],
                        delay_after=0.3,
                        repeat=1
                    )
                    
                    spot_found = True
                    break
            
            if spot_found:
                # 步骤2: 等待战斗开始
                fight_detected = False
                start_time = time.time()
                
                while time.time() - start_time < 5 and self.running and self.fighting:
                    detected, confidence, _ = self.detect_image(FIGHT_REGION, FIGHT_IMAGE_PATH, 0.8)
                    self.update_fight_log(f"检测战斗界面 - 匹配度: {confidence:.4f}")
                    
                    if detected:
                        self.update_fight_log(f"\n✅ 已进入【战斗场景】 (匹配度: {confidence:.4f})")
                        fight_detected = True
                        time.sleep(0.5)
                        break
                    time.sleep(0.3)
                
                if not fight_detected:
                    self.update_fight_log("❌ 未检测到战斗场景，重新寻找野怪...")
                    time.sleep(0.5)
                    continue
                
                # 步骤3: 使用RGB点检测普通形态
                is_normal = self.check_rgb_points()
                self.update_fight_log(f"普通形态检测: {'是' if is_normal else '否'}")
                
                if is_normal:
                    self.update_fight_log("✅ 检测为【普通形态】，执行刷野步骤...")
                    time.sleep(2)
                    
                    # 步骤4: 执行战斗操作
                    self.execute_click_group(battle_steps)
                    
                    # 步骤5: 等待战斗结束
                    over_detected = False
                    over_start_time = time.time()
                    
                    while time.time() - over_start_time < 15 and self.running and self.fighting:
                        detected, confidence, _ = self.detect_image(OVER_REGION, OVER_IMAGE_PATH, 0.8)
                        self.update_fight_log(f"检测战斗结束 - 匹配度: {confidence:.4f}")
                        
                        if detected:
                            self.update_fight_log(f"\n✅ 【战斗结束】 (匹配度: {confidence:.4f})")
                            over_detected = True
                            break
                        time.sleep(0.3)
                    
                    # 处理战斗结束超时
                    if not over_detected:
                        self.update_fight_log("❌ 未检测到战斗结束界面，尝试恢复...")
                        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    
                    # 执行结束点击组
                    self.update_fight_log("执行【结束点击组】")
                    
                    # 根据满级状态决定执行哪些点击
                    if self.fight_config["full_level"]:
                        # 满级精灵跳过"获取经验"点击
                        self.execute_click_group(full_level_clicks)
                    else:
                        # 未满级执行所有点击
                        self.execute_click_group(battle_end_clicks)
                    
                    # 步骤6: 检查物资掉落 (如果启用)
                    if self.fight_config["enable_materials"]:
                        # 快速检测物资界面
                        materials_detected = False
                        materials_start_time = time.time()
                        
                        while time.time() - materials_start_time < 1.0 and self.running and self.fighting:
                            detected, confidence, _ = self.detect_image(MATERIALS_REGION, MATERIALS_IMAGE_PATH, 0.7)
                            self.update_fight_log(f"检测物资掉落 - 匹配度: {confidence:.4f}")
                            
                            if detected:
                                self.update_fight_log(f"\n 检测到【物资掉落】")
                                materials_detected = True
                                break
                            time.sleep(0.2)
                        
                        if materials_detected:
                            self.execute_click_step(
                                coord=(956, 694),
                                label="点确定",
                                delay_after=0.3,
                                repeat=2
                            )
                    
                    # 增加战斗计数
                    self.fight_config["battle_count"] += 1
                    self.save_fight_config()
                    self.battle_count_var.set(f"当前战斗次数: {self.fight_config['battle_count']}")
                    self.update_fight_log(f"🔄 已完成 {self.fight_config['battle_count']}/{self.fight_config['medicine_threshold']} 次战斗")
                    self.update_fight_log("等待 2 秒后继续...")
                    time.sleep(2)
                else:
                    # 检测到特殊形态时发出告警
                    self.update_fight_log(f"❌ 检测为特殊形态，跳过此次操作...")
                    self.send_wechat_alarm(f"❗ {self.fight_config['username']} ❗ 抓捕过程中发现【特殊】形态精灵，等待人工处理…")
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    
                    # 重新开始循环
                    self.update_fight_log("重新扫描野怪区域...")
                    time.sleep(2)
            else:
                self.update_fight_log("未检测到野怪，继续搜索...")
                time.sleep(0.3)

# 运行应用
if __name__ == "__main__":
    # 设置Tesseract路径（根据实际情况修改）
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    root = tk.Tk()
    app = MonsterFarmApp(root)
    root.mainloop()