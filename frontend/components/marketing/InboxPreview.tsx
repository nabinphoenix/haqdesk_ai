"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Bot, LineChart, Sparkles, User, UserRound } from "lucide-react";
import { useEffect, useState } from "react";

type Conversation = {
  id: number;
  contactId: "raman" | "sita" | "hari";
  name: string;
  gender: "male" | "female";
  message: string;
  reply: string;
  arrivalDelayMs: number;
};

type FeedConversation = Conversation & {
  phase: "customer" | "replied";
  receivedAt: number;
};

const conversationSequence: Conversation[] = [
  {
    id: 1,
    contactId: "raman",
    name: "Raman Shrestha",
    gender: "male",
    message: "Why the payment is failing?",
    reply: "I'm checking the payment status now.",
    arrivalDelayMs: 250,
  },
  {
    id: 2,
    contactId: "sita",
    name: "Sita Thapa",
    gender: "female",
    message: "Yo Kurta ko kati price ho?",
    reply: "It's Rs. 2,499 and available today.",
    arrivalDelayMs: 3250,
  },
  {
    id: 3,
    contactId: "hari",
    name: "Hari Maharjan",
    gender: "male",
    message: "Thank you for fast assist!",
    reply: "You're welcome - happy to help.",
    arrivalDelayMs: 6250,
  },
  {
    id: 4,
    contactId: "raman",
    name: "Raman Shrestha",
    gender: "male",
    message: "Is my payment issue resolved now?",
    reply: "Yes - your payment is confirmed and successful.",
    arrivalDelayMs: 40000,
  },
  {
    id: 5,
    contactId: "hari",
    name: "Hari Maharjan",
    gender: "male",
    message: "Can you share my order status?",
    reply: "Your order is packed and will ship today.",
    arrivalDelayMs: 43000,
  },
];

const firstMessageDelayMs = 250;
const messageIntervalMs = 3000;
const replyDelayMs = 1250;

function relativeTime(receivedAt: number, now: number) {
  const seconds = Math.max(0, Math.floor((now - receivedAt) / 1000));

  if (seconds < 5) return "now";
  return seconds + "s ago";
}

function TypingMessage({ text }: { text: string }) {
  const shouldReduceMotion = useReducedMotion();
  const [visibleText, setVisibleText] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (shouldReduceMotion) {
      setVisibleText(text);
      setIsTyping(false);
      return;
    }

    let characterIndex = 0;
    setVisibleText("");
    setIsTyping(true);

    const intervalId = window.setInterval(() => {
      characterIndex += 1;
      setVisibleText(text.slice(0, characterIndex));

      if (characterIndex >= text.length) {
        window.clearInterval(intervalId);
        setIsTyping(false);
      }
    }, 32);

    return () => window.clearInterval(intervalId);
  }, [shouldReduceMotion, text]);

  return (
    <span aria-label={text}>
      {visibleText}
      {isTyping && (
        <span
          aria-hidden="true"
          className="ml-px inline-block h-[0.95em] w-px translate-y-[0.12em] animate-pulse bg-current"
        />
      )}
    </span>
  );
}

function ConversationRow({
  conversation,
  now,
  isNewest,
}: {
  conversation: FeedConversation;
  now: number;
  isNewest: boolean;
}) {
  const isFemale = conversation.gender === "female";

  return (
    <motion.article
      layout="position"
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 360, damping: 30 }}
      className={
        "border-b border-white/35 px-4 py-3 dark:border-white/10 " +
        (isNewest ? "border-l-2 border-l-[#6D4AE2]" : "")
      }
    >
      <div className="flex items-start gap-3">
        <div
          className={
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-full " +
            (isFemale ? "bg-pink-500/15 text-pink-500" : "bg-blue-500/15 text-blue-500")
          }
        >
          {isFemale ? <UserRound size={18} /> : <User size={18} />}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <span className="truncate text-sm font-semibold text-foreground">{conversation.name}</span>
            <span className="shrink-0 text-[10px] text-muted-foreground">
              {relativeTime(conversation.receivedAt, now)}
            </span>
          </div>
          <p className="mt-0.5 min-h-4 text-xs text-muted-foreground">
            <TypingMessage key={"customer-" + conversation.id} text={conversation.message} />
          </p>
        </div>
      </div>

      <AnimatePresence initial={false}>
        {conversation.phase === "replied" && (
          <motion.div
            initial={{ height: 0, marginTop: 0, opacity: 0 }}
            animate={{ height: "auto", marginTop: 8, opacity: 1 }}
            exit={{ height: 0, marginTop: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: "easeOut" }}
            className="ml-12 overflow-hidden border-l border-[#9D85FF]/55 pl-2.5"
          >
            <div className="flex items-center gap-1 text-[10px] font-semibold text-[#6D4AE2]">
              <Bot size={12} aria-hidden="true" />
              HaqDesk AI
              <span className="font-medium text-muted-foreground">- now</span>
            </div>
            <p className="mt-0.5 min-h-4 text-[11px] leading-4 text-muted-foreground">
              <TypingMessage key={"reply-" + conversation.id} text={conversation.reply} />
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}

export default function InboxPreview() {
  const shouldReduceMotion = useReducedMotion();
  const [feed, setFeed] = useState<FeedConversation[]>([]);
  const [now, setNow] = useState(0);

  useEffect(() => {
    if (shouldReduceMotion) {
      const timestamp = Date.now();
      setFeed(
        [...conversationSequence]
          .reverse()
          .filter(
            (conversation, index, items) =>
              items.findIndex((item) => item.contactId === conversation.contactId) === index
          )
          .map((conversation, index) => ({
            ...conversation,
            phase: "replied",
            receivedAt: timestamp - index * messageIntervalMs,
          }))
      );
      return;
    }

    setFeed([]);
    const timeouts: number[] = [];

    conversationSequence.forEach((conversation) => {
      const customerDelay = conversation.arrivalDelayMs;
      const replyDelay = customerDelay + replyDelayMs;

      timeouts.push(
        window.setTimeout(() => {
          const receivedAt = Date.now();
          setFeed((currentFeed) => [
            { ...conversation, phase: "customer", receivedAt },
            ...currentFeed.filter((item) => item.contactId !== conversation.contactId),
          ]);
        }, customerDelay)
      );

      timeouts.push(
        window.setTimeout(() => {
          setFeed((currentFeed) =>
            currentFeed.map((item) =>
              item.id === conversation.id ? { ...item, phase: "replied" } : item
            )
          );
        }, replyDelay)
      );
    });

    return () => timeouts.forEach((timeout) => window.clearTimeout(timeout));
  }, [shouldReduceMotion]);

  useEffect(() => {
    if (feed.length === 0) return;

    setNow(Date.now());
    const tickerId = window.setInterval(() => setNow(Date.now()), 1000);

    return () => window.clearInterval(tickerId);
  }, [feed.length]);

  const suggestionVisible = feed.some((conversation) => conversation.phase === "replied");

  return (
    <div className="w-full max-w-md overflow-hidden rounded-2xl border border-white/45 bg-transparent shadow-none dark:border-white/10">
      <div className="flex items-center justify-between border-b border-white/35 px-4 py-3 dark:border-white/10">
        <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">INBOX</span>
        <span className="rounded-full border border-[#6D4AE2]/35 bg-transparent px-2 py-0.5 text-xs font-semibold text-[#6D4AE2]">
          {feed.length ? feed.length + " new" : "Live"}
        </span>
      </div>

      <AnimatePresence initial={false}>
        {feed.map((conversation, index) => (
          <ConversationRow
            key={conversation.contactId}
            conversation={conversation}
            now={now}
            isNewest={index === 0}
          />
        ))}
      </AnimatePresence>

      <AnimatePresence initial={false}>
        {suggestionVisible && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.25 }}
            className="flex items-center justify-between border-t border-white/35 px-4 py-2.5 dark:border-white/10"
          >
            <span className="flex items-center gap-1 text-[11px] font-semibold text-purple-500">
              <Sparkles size={12} aria-hidden="true" />
              AI Suggestion
            </span>
            <span className="ml-2 truncate text-[11px] italic text-muted-foreground">
              Reply drafted and ready to review
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex items-center gap-2 border-t border-white/35 px-4 py-2.5 dark:border-white/10">
        <LineChart size={14} className="text-green-500" aria-hidden="true" />
        <div className="flex flex-col">
          <span className="text-[11px] font-semibold text-foreground">Response time</span>
          <span className="text-[10px] text-muted-foreground">68% faster with AI</span>
        </div>
      </div>
    </div>
  );
}