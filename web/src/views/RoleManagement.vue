<template>
  <div class="role-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>角色管理</span>
          <el-button type="primary" @click="openDialog()">新增角色</el-button>
        </div>
      </template>
      <el-table :data="roles" v-loading="loading" stripe>
        <el-table-column prop="name" label="角色名" width="150" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="permissions" label="权限" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="p in row.permissions?.slice(0, 3)" :key="p" size="small" style="margin-right: 4px; margin-bottom: 4px">
              {{ p }}
            </el-tag>
            <el-tag v-if="row.permissions?.length > 3" size="small" type="info">+{{ row.permissions.length - 3 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑角色' : '新增角色'" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="角色名" prop="name">
          <el-input v-model="form.name" placeholder="请输入角色名" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="权限" prop="permissions">
          <el-select v-model="form.permissions" multiple filterable allow-create placeholder="请输入权限" style="width: 100%">
            <el-option v-for="p in permissionOptions" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="租户" prop="tenant_id">
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getRoles, createRole, updateRole, deleteRole, type Role } from '@/api/role'
import { getTenants, type Tenant } from '@/api/tenant'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const loading = ref(false)
const roles = ref<Role[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const tenantOptions = ref<Tenant[]>([])

const permissionOptions = [
  'agent:read', 'agent:write', 'agent:delete',
  'model:read', 'model:write', 'model:delete',
  'tool:read', 'tool:write', 'tool:delete',
  'knowledge:read', 'knowledge:write', 'knowledge:delete',
  'user:read', 'user:write', 'user:delete',
  'role:read', 'role:write', 'role:delete',
  'tenant:read', 'tenant:write', 'tenant:delete',
  'execution_log:read',
]

const dialogVisible = ref(false)
const editingId = ref<string>('')
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  description: '',
  permissions: [] as string[],
  tenant_id: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入角色名', trigger: 'blur' }],
  tenant_id: [{ required: true, message: '请选择租户', trigger: 'change' }],
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    const res = await getRoles({ page: page.value, page_size: pageSize.value })
    roles.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('加载角色列表失败')
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

function openDialog(row?: Role) {
  if (row) {
    editingId.value = row.id
    form.name = row.name
    form.description = row.description
    form.permissions = [...(row.permissions || [])]
    form.tenant_id = row.tenant_id
  } else {
    editingId.value = ''
    form.name = ''
    form.description = ''
    form.permissions = []
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
      await updateRole(editingId.value, { name: form.name, description: form.description, permissions: form.permissions })
      ElMessage.success('更新成功')
    } else {
      await createRole({ name: form.name, description: form.description, permissions: form.permissions, tenant_id: form.tenant_id })
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

async function handleDelete(row: Role) {
  await ElMessageBox.confirm(`确定删除角色「${row.name}」？`, '确认删除', { type: 'warning' })
  try {
    await deleteRole(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
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
</style>
