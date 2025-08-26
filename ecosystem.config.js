module.exports = {
  apps: [
    {
      name: '1xbet-bot',
      script: '1xbet.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/1xbet-error.log',
      out_file: './logs/1xbet-out.log',
      log_file: './logs/1xbet-combined.log',
      time: true
    },
    {
      name: '1win-bot',
      script: '1win.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/1win-error.log',
      out_file: './logs/1win-out.log',
      log_file: './logs/1win-combined.log',
      time: true
    },
    {
      name: 'melbet-bot',
      script: 'melbet.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/melbet-error.log',
      out_file: './logs/melbet-out.log',
      log_file: './logs/melbet-combined.log',
      time: true
    },
    {
      name: 'mostbet-bot',
      script: 'mostbet.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/mostbet-error.log',
      out_file: './logs/mostbet-out.log',
      log_file: './logs/mostbet-combined.log',
      time: true
    },
    {
      name: 'admin-bot',
      script: 'admin_bot.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/admin-error.log',
      out_file: './logs/admin-out.log',
      log_file: './logs/admin-combined.log',
      time: true
    },
    {
      name: 'main-bot',
      script: 'main_bot.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/main-error.log',
      out_file: './logs/main-out.log',
      log_file: './logs/main-combined.log',
      time: true
    }
  ]
};

