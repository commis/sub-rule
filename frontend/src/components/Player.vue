<template>
  <div class="player-container">
    <div v-if="selectedChannel" class="player">
      <h3>{{ selectedChannel.name }}</h3>
      <video ref="videoPlayer" controls width="100%" height="400">
        <source :src="selectedChannel.url" type="application/x-mpegURL">
        您的浏览器不支持视频播放
      </video>
    </div>
    <div v-else class="empty-state">
      <p>请选择一个频道开始播放</p>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    selectedChannel: {
      type: Object,
      default: null
    }
  },
  mounted() {
    this.initPlayer()
  },
  watch: {
    selectedChannel() {
      this.initPlayer()
    }
  },
  methods: {
    initPlayer() {
      if (this.$refs.videoPlayer && this.selectedChannel) {
        this.$refs.videoPlayer.load()
        this.$refs.videoPlayer.play().catch(e => {
          console.error('视频播放错误:', e)
        })
      }
    }
  }
}
</script>

<style scoped>
.player-container {
  flex-grow: 1;
  padding: 10px;
}

.player video {
  background-color: #000;
  margin-top: 10px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
  background-color: #f9f9f9;
  border-radius: 5px;
}
</style>  