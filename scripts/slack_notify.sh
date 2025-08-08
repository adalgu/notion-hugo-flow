#!/bin/bash

# Claude Code Slack Notification Script
# Usage: ./slack_notify.sh "message" [channel] [emoji]

# Configuration
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/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"
DEFAULT_CHANNEL="#general"
DEFAULT_EMOJI=":robot_face:"

# Function to send notification
send_slack_notification() {
    local message="$1"
    local channel="${2:-$DEFAULT_CHANNEL}"
    local emoji="${3:-$DEFAULT_EMOJI}"
    
    # Get current timestamp
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Get current directory/project info
    local project_info="$(basename $(pwd))"
    
    # Create payload
    local payload=$(cat <<EOF
{
    "channel": "$channel",
    "username": "Claude Code",
    "icon_emoji": "$emoji",
    "text": ":information_source: *Claude Code Notification*",
    "attachments": [
        {
            "color": "good",
            "fields": [
                {
                    "title": "Message",
                    "value": "$message",
                    "short": false
                },
                {
                    "title": "Project",
                    "value": "$project_info",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "$timestamp",
                    "short": true
                }
            ]
        }
    ]
}
EOF
)
    
    # Send to Slack
    curl -X POST \
        -H 'Content-type: application/json' \
        --data "$payload" \
        --silent \
        "$SLACK_WEBHOOK_URL"
}

# Main execution
if [ $# -eq 0 ]; then
    echo "Usage: $0 'message' [channel] [emoji]"
    exit 1
fi

send_slack_notification "$1" "$2" "$3"