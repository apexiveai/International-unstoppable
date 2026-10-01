"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import API_URL from "@/lib/api";

type Message = {

  id: number;

  role: "user" | "assistant";

  content: string;

};

export default function FloatingChatbot() {

  const [open, setOpen] = useState(false);

  const [message, setMessage] = useState("");

  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState<Message[]>([

    {

      id: 1,

      role: "assistant",

      content:

        "Hello 👋 I'm the Apexive AI Assistant. Ask me anything about Apexive Community, its features, projects, resources, and Clone Detector.",

    },

  ]);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {

    messagesEndRef.current?.scrollIntoView({

      behavior: "smooth",

    });

  }, [messages, loading]);

  async function sendMessage(event?: FormEvent) {

    event?.preventDefault();

    const trimmed = message.trim();

    if (!trimmed || loading) {

      return;

    }

    const userMessage: Message = {

      id: Date.now(),

      role: "user",

      content: trimmed,

    };

    setMessages((previous) => [

      ...previous,

      userMessage,

    ]);

    setMessage("");

    setLoading(true);

    try {

      const response = await fetch(

        `${API_URL}/api/chatbot/message`,

        {

          method: "POST",

          headers: {

            "Content-Type": "application/json",

          },

          body: JSON.stringify({

            message: trimmed,

          }),

        }

      );

      const data = await response.json();

      if (!response.ok) {

        throw new Error(

          data?.detail || "Unable to contact AI assistant."

        );

      }

      const assistantMessage: Message = {

        id: Date.now() + 1,

        role: "assistant",

        content:

          data.answer ||

          "I couldn't generate a response.",

      };

      setMessages((previous) => [

        ...previous,

        assistantMessage,

      ]);

    } catch (error) {

      console.error("Chatbot error:", error);

      setMessages((previous) => [

        ...previous,

        {

          id: Date.now() + 2,

          role: "assistant",

          content:

            "I'm unable to connect to the Apexive AI service right now. Please try again shortly.",

        },

      ]);

    } finally {

      setLoading(false);

    }

  }

  function handleKeyDown(

    event: React.KeyboardEvent<HTMLTextAreaElement>

  ) {

    if (event.key === "Enter" && !event.shiftKey) {

      event.preventDefault();

      sendMessage();

    }

  }

  return (

    <>

      {/* Floating Button */}

      {!open && (

        <button

          type="button"

          onClick={() => setOpen(true)}

          aria-label="Open Apexive AI Assistant"

          className="

            fixed

            bottom-6

            right-6

            z-[9999]

            flex

            h-16

            w-16

            items-center

            justify-center

            rounded-full

            border

            border-slate-200

            bg-white

            text-slate-900

            shadow-2xl

            transition

            duration-200

            hover:scale-105

            hover:shadow-[0_20px_50px_rgba(0,0,0,0.20)]

            active:scale-95

          "

        >

          <div

            className="

              flex

              h-11

              w-11

              items-center

              justify-center

              rounded-full

              bg-slate-950

              text-xl

              text-white

            "

          >

            ✦

          </div>

          <span

            className="

              absolute

              right-1

              top-1

              h-3

              w-3

              rounded-full

              bg-emerald-500

              ring-2

              ring-white

            "

          />

        </button>
        )}

      {/* Chat Window */}

      {open && (

        <div

          className="

            fixed

            bottom-6

            right-6

            z-[9999]

            flex

            h-[min(680px,calc(100vh-48px))]

            w-[min(420px,calc(100vw-32px))]

            flex-col

            overflow-hidden

            rounded-3xl

            border

            border-slate-200

            bg-white

            shadow-[0_25px_80px_rgba(15,23,42,0.25)]

          "

        >

          {/* Header */}

          <div

            className="

              flex

              items-center

              justify-between

              border-b

              border-slate-200

              bg-slate-950

              px-5

              py-4

              text-white

            "

          >

            <div className="flex items-center gap-3">

              <div

                className="

                  flex

                  h-10

                  w-10

                  items-center

                  justify-center

                  rounded-full

                  bg-white

                  text-lg

                  text-slate-950

                "

              >

                ✦

              </div>

              <div>

                <div className="text-sm font-semibold">

                  Apexive AI

                </div>

                <div className="flex items-center gap-1.5 text-xs text-slate-300">

                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />

                  Online

                </div>

              </div>

            </div>

            <button

              type="button"

              onClick={() => setOpen(false)}

              aria-label="Close chat"

              className="

                flex

                h-9

                w-9

                items-center

                justify-center

                rounded-full

                text-slate-300

                transition

                hover:bg-white/10

                hover:text-white

              "

            >

              ×

            </button>

          </div>

          {/* Messages */}

          <div

            className="

              flex-1

              space-y-4

              overflow-y-auto

              bg-slate-50

              p-4

            "

          >

            {messages.map((item) => (

              <div

                key={item.id}

                className={`flex ${

                  item.role === "user"

                    ? "justify-end"

                    : "justify-start"

                }`}

              >

                <div

                  className={`

                    max-w-[85%]

                    rounded-2xl

                    px-4

                    py-3

                    text-sm

                    leading-6

                    ${

                      item.role === "user"

                        ? "rounded-br-md bg-slate-950 text-white"

                        : "rounded-bl-md border border-slate-200 bg-white text-slate-700"

                    }

                  `}

                >

                  {item.content}

                </div>

              </div>

            ))}

            {loading && (

              <div className="flex justify-start">

                <div

                  className="

                    rounded-2xl

                    rounded-bl-md

                    border

                    border-slate-200

                    bg-white

                    px-4

                    py-3

                  "

                >

                  <div className="flex gap-1.5">

                    <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />

                    <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />

                    <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
</div>

                </div>

              </div>

            )}

            <div ref={messagesEndRef} />

          </div>

          {/* Input */}

          <form

            onSubmit={sendMessage}

            className="

              border-t

              border-slate-200

              bg-white

              p-3

            "

          >

            <div

              className="

                flex

                items-end

                gap-2

                rounded-2xl

                border

                border-slate-200

                bg-slate-50

                p-2

                focus-within:border-slate-400

                focus-within:bg-white

              "

            >

              <textarea

                value={message}

                onChange={(event) =>

                  setMessage(event.target.value)

                }

                onKeyDown={handleKeyDown}

                placeholder="Ask about Apexive Community..."

                rows={1}

                maxLength={4000}

                disabled={loading}

                className="

                  max-h-28

                  min-h-10

                  flex-1

                  resize-none

                  bg-transparent

                  px-2

                  py-2

                  text-sm

                  text-slate-900

                  outline-none

                  placeholder:text-slate-400

                "

              />

              <button

                type="submit"

                disabled={

                  loading || !message.trim()

                }

                className="

                  flex

                  h-10

                  w-10

                  shrink-0

                  items-center

                  justify-center

                  rounded-xl

                  bg-slate-950

                  text-white

                  transition

                  hover:bg-slate-800

                  disabled:cursor-not-allowed

                  disabled:opacity-40

                "

                aria-label="Send message"

              >

                ↑

              </button>

            </div>

            <div className="px-1 pt-2 text-[10px] text-slate-400">

              Apexive AI Assistant · Public product information only

            </div>

          </form>

        </div>

      )}

    </>

  );

}