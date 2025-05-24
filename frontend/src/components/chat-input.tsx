"use client"

import type React from "react"

import { useState, useRef, type KeyboardEvent, useEffect } from "react"
import { Send, Paperclip, Smile } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card } from "@/components/ui/card"
import axios from "axios"

interface ChatInputProps {
  onSendMessage: (message: string) => void
}

export function ChatInput({ onSendMessage }: ChatInputProps) {
  const [message, setMessage] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    let splitRegion = '';

    if (message.trim()) {
      onSendMessage(message.trim())
      setMessage("")
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
      }
    }

    const splitMessage = message.split(", ");
    console.log(splitMessage);

    if(splitMessage.length === 2) {
      splitRegion = splitMessage[1].split(" ").join("%20");
    }
    
    // axios.post(`http://localhost:8000/live-model-test?crop=Tomato&region=Central%20Luzon`)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }

  return (
    <Card className="p-4">
      <div className="flex items-end gap-2">
        <div className="flex gap-2">
          <Button size="icon" variant="ghost" className="h-9 w-9 shrink-0">
            <Paperclip className="h-4 w-4" />
          </Button>
          <Button size="icon" variant="ghost" className="h-9 w-9 shrink-0">
            <Smile className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="min-h-[40px] max-h-[120px] resize-none pr-12 py-2"
            rows={1}
          />
        </div>

        <Button onClick={handleSend} disabled={!message.trim()} size="icon" className="h-9 w-9 shrink-0">
          <Send className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex justify-between items-center mt-2 text-xs text-muted-foreground">
        <span>Press Enter to send, Shift + Enter for new line</span>
        <span>{message.length}/2000</span>
      </div>
    </Card>
  )
}