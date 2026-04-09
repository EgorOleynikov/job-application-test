import sqlite3
import PyQt5
from PyQt5.QtCore import Qt, QByteArray, QSize
from PyQt5.QtWidgets import QTreeView, QApplication, QMenu, QHeaderView, QStyledItemDelegate
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QPixmap, QIcon
import base64
import sys
import importlib.util



def load_env():
    spec = importlib.util.spec_from_file_location("env", "env.py")
    env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(env)
    return env

env = load_env()
sqlite3_db_path = env.sqlite3_db_path
table_name = env.table_name
colour_scheme = env.colour_scheme


# db
try:
    conn = sqlite3.connect(sqlite3_db_path)
    cursor = conn.cursor()
    cursor.execute(f'SELECT id, name, id_parent, state, image FROM {table_name}')
    rows = cursor.fetchall()
except sqlite3.Error as e:
    print(f"Ошибка БД: {e}")
    rows = []
finally:
    conn.close()

nodes = {}
for row in rows:
    node_id, name, parent_id, state, image = row
    nodes[node_id] = {
        'id': node_id,
        'name': name,
        'parent_id': parent_id,
        'state': state,
        'image': image,
        'children': []
    }

root_items = []
for node_id, node in nodes.items():
    parent_id = node['parent_id']
    if parent_id == 0 or parent_id is None:  # корневой элемент
        root_items.append(node)
    else:
        if parent_id in nodes:
            nodes[parent_id]['children'].append(node)



class TreeModel(QStandardItemModel):
    def __init__(self, root_nodes, all_nodes):
        super().__init__()
        self.root_nodes = root_nodes
        self._build_tree()
        self.all_nodes = all_nodes
        # сигнал обработчика
        self.dataChanged.connect(self._on_data_changed)


    def _on_data_changed(self, topLeft, bottomRight):
        item = self.itemFromIndex(topLeft)
        new_name = item.text()
        node_id = item.data(Qt.UserRole + 2)  # id мы сохраняли здесь
        # запрос в db
        try:
            conn = sqlite3.connect(sqlite3_db_path)
            cursor = conn.cursor()
            cursor.execute(f'UPDATE {table_name} SET name = ? WHERE id = ?', (new_name, node_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Ошибка обновления БД: {e}")


    def _build_tree(self):
        for node in self.root_nodes:
            self._add_node(None, node)


    def _add_node(self, parent_item, node):
        # строка с колонками name, image, state, id, id_parent
        item = QStandardItem(node['name'])
        # служебные данные в UserRole
        item.setData(node['state'], Qt.UserRole + 1)
        item.setData(node['id'], Qt.UserRole + 2)
        item.setData(node['parent_id'], Qt.UserRole + 3)
        item.setData(node['image'], Qt.UserRole + 4)

        if node['image']:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(node['image']))
            item.setIcon(QIcon(pixmap))

        if parent_item is None:
            self.appendRow([item, QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem()])
            parent = self.itemFromIndex(self.indexFromItem(item))
        else:
            parent_item.appendRow([item, QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem()])
            parent = parent_item.child(parent_item.rowCount() - 1)

        # рекурсивно добавляем детей
        for child in node['children']:
            self._add_node(parent, child)


    def add_child(self, parent_index):
        if parent_index.isValid():
            parent_item = self.itemFromIndex(parent_index)
            parent_id = parent_item.data(Qt.UserRole + 2)
        else:
            parent_item = None
            parent_id = None

        new_node = {
            'name': "Новый элемент",
            'parent_id': parent_id,
            'state': 3,
            'image': base64.b64decode('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'),
            'children': []
        }

        try:
            conn = sqlite3.connect(sqlite3_db_path)
            cursor = conn.cursor()
            cursor.execute(
                f'INSERT INTO {table_name} (name, id_parent, image, state) VALUES (?, ?, ?, ?)',
                (new_node['name'], new_node['parent_id'], new_node['image'], new_node['state'])
            )
            conn.commit()
            new_node['id'] = cursor.lastrowid  # добавляем id после вставки
            conn.close()
        except sqlite3.Error as e:
            print(f"Ошибка вставки в БД: {e}")
            return

        if not parent_id:
            self.root_nodes.append(new_node)
        else:
            self._add_node_to_memory(parent_id, new_node)

        self._add_node(parent_item, new_node)
        apply_colors(self.invisibleRootItem())


    def _add_node_to_memory(self, parent_id, new_node):
        # рекурсивный поиск родительского узла
        def find_parent(nodes):
            for node in nodes:
                if node['id'] == parent_id:
                    node['children'].append(new_node)
                    return True
                if find_parent(node['children']):
                    return True
            return False

        find_parent(self.root_nodes)


    def delete(self, index):
        if not index.isValid():
            return

        item = self.itemFromIndex(index)
        node_id = item.data(Qt.UserRole + 2)

        # id для удаления с потомками
        ids_to_delete = self._get_all_descendant_ids(node_id)
        print(f"Найдено id для удаления: {ids_to_delete}")

        # удаляем из db
        try:
            conn = sqlite3.connect(sqlite3_db_path)
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(ids_to_delete))
            cursor.execute(f'DELETE FROM {table_name} WHERE id IN ({placeholders})', ids_to_delete)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Ошибка удаления из БД: {e}")
            return

        # удаляем из памяти с потомками
        self._remove_from_memory(node_id)

        # удаляем из модели
        parent = item.parent()
        if parent is None:
            self.removeRow(self.indexFromItem(item).row())
        else:
            parent.removeRow(item.row())

        # обновляем цвета
        self._apply_colors(self.invisibleRootItem())


    def _remove_from_memory(self, node_id):
        # удаляет узел и всех его потомков из памяти
        # удаляем потомков
        descendants = self._get_all_descendant_ids(node_id)
        for desc_id in descendants[1:]:
            self._remove_single_node(desc_id)
        # удаляем сам узел
        self._remove_single_node(node_id)


    def _remove_single_node(self, node_id):
        # удаляет один узел из root_nodes
        def remove_from_nodes(nodes):
            for i, node in enumerate(nodes):
                if node['id'] == node_id:
                    nodes.pop(i)
                    return True
                if remove_from_nodes(node['children']):
                    return True
            return False

        remove_from_nodes(self.root_nodes)


    def _get_all_descendant_ids(self, node_id):
        # собирает id узла и всех его потомков через обход дерева
        ids = [node_id]

        def find_node(nodes):
            for node in nodes:
                if node['id'] == node_id:
                    def collect_children(current_node):
                        for child in current_node['children']:
                            ids.append(child['id'])
                            collect_children(child)
                    collect_children(node)
                    return True
                if find_node(node['children']):
                    return True
            return False

        find_node(self.root_nodes)
        return ids


    def _apply_colors(self, parent_item):
        # применяет цвета ко всем элементам
        for row in range(parent_item.rowCount()):
            item = parent_item.child(row, 0)
            self._set_item_color(item)
            self._apply_colors(item)


    def _set_item_color(self, item):
        # устанавливает цвет фона для элемена
        state = item.data(Qt.UserRole + 1)
        colour = QColor(colour_scheme(state))
        item.setBackground(colour)



class MainWindow(QTreeView):
    def __init__(self, model):
        super().__init__()
        self.setModel(model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, position):
        index = self.indexAt(position)
        menu = QMenu()
        action_add = menu.addAction("Добавить элемент")
        action_delete = menu.addAction("Удалить")
        action = menu.exec_(self.viewport().mapToGlobal(position))
        if action == action_add:
            self.model().add_child(index)
        elif action == action_delete:
            self.model().delete(index)


# настройка цвета
def set_item_color(item):
    state = item.data(Qt.UserRole + 1)
    colour = QColor(colour_scheme(state))
    item.setBackground(colour)

# применение цвета
def apply_colors(parent_item):
    for row in range(parent_item.rowCount()):
        item = parent_item.child(row, 0)
        set_item_color(item)
        apply_colors(item)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    model = TreeModel(root_items, nodes)
    view = MainWindow(model)
    view.setGeometry(100, 100, 1000, 800)
    view.setIndentation(15)
    view.setIconSize(QSize(64, 64))
    
    # прячем колонки
    view.setColumnHidden(1, True)
    view.setColumnHidden(2, True)
    view.setColumnHidden(3, True)
    view.setColumnHidden(4, True)
    
    
    apply_colors(model.invisibleRootItem())
    
    class MyDelegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            return QSize(size.width(), size.height() + 20)

    view.setItemDelegate(MyDelegate())

    view.show()
    sys.exit(app.exec_())