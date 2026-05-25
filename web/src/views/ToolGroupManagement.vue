<template>
  <div class="tool-group-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>工具组管理</span>
          <el-button type="primary" @click="openDialog()">新增工具组</el-button>
        </div>
      </template>
      <el-table :data="toolGroups" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="tools" label="工具数" width="100">
          <template #default="{ row }">{{ row.tools?.length || 0 }}</template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="(val: boolean) => handleToggle(row, val)"
              :loading="row._toggling"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="success" @click="openToolDialog(row)">注册工具</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="loadData"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑工具组' : '新增工具组'" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入工具组名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="租户" prop="tenant_id" v-if="!editingId">
          <el-select v-model="form.tenant_id" placeholder="请选择租户" style="width: 100%">
            <el-option v-for="t in tenantOptions" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="toolDialogVisible" :title="`注册工具 - ${currentGroup?.name}`" width="600px" destroy-on-close>
      <div v-if="currentGroup?.tools?.length" style="margin-bottom: 16px">
        <div class="tool-list-label">已注册工具</div>
        <el-table :data="currentGroup.tools" size="small" stripe>
          <el-table-column prop="name" label="名称" width="150" />
          <el-table-column prop="description" label="描述" show-overflow-tooltip />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button link type="danger" size="small" @click="handleUnregisterTool(row)">注销</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-divider />
      <div class="tool-list-label">注册新工具</div>
      <el-form :model="toolForm" label-width="80px">
        <el-form-item label="工具名">
          <el-input v-model="toolForm.tool_name" placeholder="请输入工具名称" />
        </el-form-item>
        <el-form-item label="工具配置">
          <el-input v-model="toolForm.tool_config_str" type="textarea" :rows="4" placeholder="JSON 格式配置" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="registering" @click="handleRegisterTool">注册</el-button>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  getToolGroups, createToolGroup, updateToolGroup, deleteToolGroup,
  registerTool, unregisterTool, toggleToolGroup,
  type ToolGroup, type ToolItem,
} from '@/api/toolGroup'
import { getTenants, type Tenant } from '@/api/tenant'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const loading = ref(false)
const toolGroups = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const tenantOptions = ref<Tenant[]>([])

const dialogVisible = ref(false)
const editingId = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({
  name: '',
  description: '',
  tenant_id: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入工具组名称', trigger: 'blur' }],
}

const toolDialogVisible = ref(false)
const currentGroup = ref<ToolGroup | null>(null)
const registering = ref(false)
const toolForm = reactive({
  tool_name: '',
  tool_config_str: '{}',
})

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    const res = await getToolGroups({ page: page.value, page_size: pageSize.value })
    toolGroups.value = res.data.items.map((item: any) => ({ ...item, _toggling: false }))
    total.value = res.data.total
  } catch {
    ElMessage.error('加载工具组列表失败')
  } finally {
    loading.value = false
  }
}

async function loadTenants() {
  try {
    const res = await getTenants({ page: 1, page_size: 100 })
    tenantOptions.value = res.data.items
  } catch {}
}

function openDialog(row?: ToolGroup) {
  if (row) {
    editingId.value = row.id
    form.name = row.name
    form.description = row.description
  } else {
    editingId.value = ''
    form.name = ''
    form.description = ''
    form.tenant_id = ''
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (editingId.value) {
      await updateToolGroup(editingId.value, { name: form.name, description: form.description })
      ElMessage.success('更新成功')
    } else {
      await createToolGroup({ name: form.name, description: form.description, tenant_id: form.tenant_id })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleToggle(row: any, val: boolean) {
  row._toggling = true
  try {
    await toggleToolGroup(row.id, val)
    row.is_active = val
    ElMessage.success(val ? '已启用' : '已禁用')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    row._toggling = false
  }
}

async function handleDelete(row: ToolGroup) {
  await ElMessageBox.confirm(`确定删除工具组「${row.name}」？`, '确认删除', { type: 'warning' })
  try {
    await deleteToolGroup(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

function openToolDialog(row: ToolGroup) {
  currentGroup.value = row
  toolForm.tool_name = ''
  toolForm.tool_config_str = '{}'
  toolDialogVisible.value = true
}

async function handleRegisterTool() {
  if (!currentGroup.value || !toolForm.tool_name) {
    ElMessage.warning('请输入工具名称')
    return
  }
  let config = {}
  try {
    config = JSON.parse(toolForm.tool_config_str)
  } catch {
    ElMessage.error('工具配置 JSON 格式错误')
    return
  }
  registering.value = true
  try {
    await registerTool(currentGroup.value.id, { tool_name: toolForm.tool_name, tool_config: config })
    ElMessage.success('注册成功')
    loadData()
    const updated = toolGroups.value.find((g: any) => g.id === currentGroup.value?.id)
    if (updated) currentGroup.value = updated
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally {
    registering.value = false
  }
}

async function handleUnregisterTool(tool: ToolItem) {
  if (!currentGroup.value) return
  await ElMessageBox.confirm(`确定注销工具「${tool.name}」？`, '确认注销', { type: 'warning' })
  try {
    await unregisterTool(currentGroup.value.id, tool.name)
    ElMessage.success('注销成功')
    loadData()
    const updated = toolGroups.value.find((g: any) => g.id === currentGroup.value?.id)
    if (updated) currentGroup.value = updated
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '注销失败')
  }
}

onMounted(() => {
  loadData()
  loadTenants()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tool-list-label {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
</style>
