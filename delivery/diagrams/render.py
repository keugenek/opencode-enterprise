"""Render the public reference topology. Requires matplotlib; no network access."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(14, 10), dpi=160)
fig.patch.set_facecolor('#f4f7fb')
ax.set(xlim=(0,14), ylim=(0,10)); ax.axis('off')
ax.text(.55,9.52,'OpenCode Enterprise · схема внедрения',fontsize=23,fontweight='bold',color='#132744')
ax.text(.55,9.13,'Внутренняя модель · управляемые рабочие среды · изоляция проектов',fontsize=12,color='#52627a')

def box(x,y,w,h,title,sub,color='#e9f0fc'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.12',linewidth=1.2,edgecolor='#b7c7da',facecolor=color))
    ax.text(x+w/2,y+h*.64,title,ha='center',va='center',fontsize=12,fontweight='bold',color='#152d4f')
    ax.text(x+w/2,y+h*.27,sub,ha='center',va='center',fontsize=9.5,color='#405570',linespacing=1.5)

def arrow(a,b,label=None,dashed=False):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=14,linewidth=1.5,color='#57718c',linestyle='--' if dashed else '-'))
    if label: ax.text((a[0]+b[0])/2+.10,(a[1]+b[1])/2,label,fontsize=8.5,color='#405570',va='center')

box(.55,7.62,12.9,.98,'Разработчики: Windows CLI / Linux CLI','Обычная учётная запись · отдельная VM/VDI или workspace · политика администратора', '#e2eafa')
box(.55,6.10,12.9,.90,'Корпоративный VPN','MFA + идентификация пользователя и устройства · внутренние DNS и TLS', '#e2eafa')
arrow((7,7.62),(7,7.02))
ax.text(.65,5.71,'INFERENCE',fontsize=10,fontweight='bold',color='#38625a')
ax.text(8.55,5.71,'СОВМЕСТНАЯ РАЗРАБОТКА',fontsize=10,fontweight='bold',color='#70583a')
box(.55,4.49,4.5,.92,'Внутренний прокси','Авторизация · лимиты · проверенная identity', '#e5f3ed')
box(.55,2.98,4.5,.92,'LLM-роутер','Одна модель · только внутренние реплики', '#e5f3ed')
box(.55,1.47,4.5,.92,'Пул vLLM','Закреплённые веса, версия и tool parser', '#e5f3ed')
box(5.45,2.98,2.55,.92,'Кеш inference','По умолчанию выключен\nACL + проект + TTL', '#e5f3ed')
box(8.55,4.49,4.9,.92,'GitLab: общий план и код','Задачи · версии плана · отдельные ветки', '#fbefdf')
box(8.55,2.98,4.9,.92,'CI + review + закрытый eval','Проверки · evidence · одобрение изменений', '#fbefdf')
box(8.55,1.47,4.9,.92,'Внутренние артефакты и кеш','Зависимости / сборки · digest · ACL проекта', '#fbefdf')
arrow((2.8,6.1),(2.8,5.43))
arrow((12.9,6.1),(12.9,5.43))
arrow((2.8,4.49),(2.8,3.92),'HTTPS')
arrow((2.8,2.98),(2.8,2.41),'HTTPS')
arrow((5.05,3.44),(5.43,3.44),dashed=True)
arrow((11,4.49),(11,3.92))
arrow((11,2.98),(11,2.41))
ax.text(.65,.91,'ГРАНИЦЫ: нет cloud fallback; egress ограничен для CLI и дочерних процессов;',fontsize=10,fontweight='bold',color='#263b57')
ax.text(.65,.63,'нет общих writable workspaces; кеши разделены по проектам; планы не изменяют security policy.',fontsize=10,color='#263b57')
ax.text(.65,.21,'Целевая архитектура: VPN / proxy / router / shared plan / private eval не развёрнуты этим репозиторием.',fontsize=9.5,color='#765a39')
fig.savefig(Path(__file__).with_name('deployment.png'),dpi=160,bbox_inches='tight',pad_inches=.2)
