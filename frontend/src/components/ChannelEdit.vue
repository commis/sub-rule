<template>
  <div class="channel-edit">
    <h3>编辑频道</h3>
    <div class="form-group">
      <label>频道名称</label>
      <input v-model="channel.name" type="text" placeholder="请输入频道名称">
    </div>
    <div class="form-group">
      <label>直播地址</label>
      <input v-model="channel.url" type="text" placeholder="请输入直播地址">
    </div>
    <div class="form-group">
      <label>分类</label>
      <input v-model="channel.category" type="text" placeholder="请输入分类">
    </div>
    <div class="buttons">
      <button @click="saveChannel">保存</button>
      <button @click="cancelEdit">取消</button>
      <button v-if="isEditMode" @click="deleteChannel" class="delete-btn">删除</button>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    channel: {
      type: Object,
      default: () => ({ name: '', url: '', category: '' })
    },
    isEditMode: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    saveChannel() {
      if (this.channel.name && this.channel.url) {
        this.$emit('save', this.channel)
      } else {
        alert('频道名称和直播地址不能为空')
      }
    },
    cancelEdit() {
      this.$emit('cancel')
    },
    deleteChannel() {
      if (confirm('确定要删除这个频道吗？')) {
        this.$emit('delete')
      }
    }
  }
}
</script>

<style scoped>
.channel-edit {
  padding: 10px;
  border-left: 1px solid #eee;
  min-width: 250px;
}

.form-group {
  margin-bottom: 15px;
  text-align: left;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.buttons {
  display: flex;
  gap: 5px;
  margin-top: 20px;
}

.buttons button {
  flex-grow: 1;
  padding: 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.buttons button:first-child {
  background-color: #42b983;
  color: white;
}

.buttons button:nth-child(2) {
  background-color: #ddd;
}

.delete-btn {
  background-color: #e74c3c !important;
  color: white !important;
}
</style>  