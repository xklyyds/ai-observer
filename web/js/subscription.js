const Subscription = {
    init() {
        this.loadCount();
    },

    async subscribe() {
        const emailInput = document.getElementById('subscribeEmail');
        const msgDiv = document.getElementById('subscribeMsg');
        const btn = document.getElementById('subscribeBtn');
        const email = emailInput.value.trim().toLowerCase();

        if (!email || !email.includes('@') || !email.includes('.')) {
            this.showMessage('请输入有效的邮箱地址', 'error');
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span>提交中...</span>';
        msgDiv.className = 'subscribe-msg';
        msgDiv.textContent = '';

        try {
            const res = await fetch('/api/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await res.json();

            if (data.status === 'success') {
                this.showMessage(data.message || '订阅成功！请查收验证邮件。', 'success');
                emailInput.value = '';
            } else {
                this.showMessage(data.message || '订阅失败，请稍后再试', 'error');
            }
        } catch (err) {
            this.showMessage('网络错误，请稍后再试', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<span>订阅</span>';
        }
    },

    async unsubscribe() {
        const emailInput = document.getElementById('subscribeEmail');
        const msgDiv = document.getElementById('subscribeMsg');
        const email = emailInput.value.trim().toLowerCase();

        if (!email || !email.includes('@')) {
            this.showMessage('请输入您的邮箱地址', 'error');
            return;
        }

        try {
            const res = await fetch('/api/unsubscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await res.json();

            if (data.status === 'success') {
                this.showMessage('已取消订阅', 'success');
            } else {
                this.showMessage('操作失败，请稍后再试', 'error');
            }
        } catch (err) {
            this.showMessage('网络错误，请稍后再试', 'error');
        }
    },

    async loadCount() {
        try {
            const res = await fetch('/api/stats');
            const data = await res.json();
            const countEl = document.getElementById('subscriberCount');
            if (countEl && data.subscriberCount !== undefined) {
                countEl.textContent = data.subscriberCount;
            }
        } catch (err) {
            // Silently fail - stats are non-critical
        }
    },

    showMessage(text, type) {
        const msgDiv = document.getElementById('subscribeMsg');
        msgDiv.textContent = text;
        msgDiv.className = 'subscribe-msg ' + type;
    }
};

document.addEventListener('DOMContentLoaded', () => Subscription.init());
