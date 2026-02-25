import { useState, useRef, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  Modal,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { ScreenContainer } from "@/components/screen-container";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useColors } from "@/hooks/use-colors";

// ─── Types ───────────────────────────────────────────────────────────────────

type Engine = {
  id: string;
  name: string;
  port: number;
  status: "healthy" | "degraded" | "down";
  description: string;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  engine?: string;
  tokens?: number;
  timestamp: number;
};

// ─── Data ────────────────────────────────────────────────────────────────────

const ENGINES: Engine[] = [
  { id: "vllm",        name: "vLLM",         port: 8100,  status: "healthy",  description: "PagedAttention · Continuous batching" },
  { id: "tgi",         name: "TGI",          port: 1101,  status: "healthy",  description: "Token streaming · Flash attention" },
  { id: "sglang",      name: "SGLang",       port: 1102,  status: "healthy",  description: "RadixAttention · Structured gen" },
  { id: "tensorrt",    name: "TensorRT-LLM", port: 1103,  status: "degraded", description: "INT8/FP8 quantization · Multi-GPU" },
  { id: "deepspeed",   name: "DeepSpeed",    port: 1104,  status: "down",     description: "ZeRO inference · Pipeline parallelism" },
  { id: "lmdeploy",    name: "LMDeploy",     port: 1105,  status: "healthy",  description: "TurboMind · Persistent batch" },
  { id: "ollama",      name: "Ollama",       port: 11434, status: "healthy",  description: "Local models · Pull-on-demand" },
];

const STATUS_COLOR = {
  healthy:  "#10B981",
  degraded: "#F59E0B",
  down:     "#EF4444",
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function ChatScreen() {
  const colors = useColors();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "0",
      role: "assistant",
      content: "KUBE-1.0 ULTRA online. Select an inference engine and start chatting.",
      engine: "vllm",
      tokens: 18,
      timestamp: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [selectedEngine, setSelectedEngine] = useState<Engine>(ENGINES[0]);
  const [enginePickerVisible, setEnginePickerVisible] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const listRef = useRef<FlatList>(null);

  const sendMessage = useCallback(() => {
    if (!input.trim() || isStreaming) return;
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);

    // Simulate streaming response
    setTimeout(() => {
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `[${selectedEngine.name}] Processing via eco-base AI Service (port ${selectedEngine.port}). This is a simulated response. Connect to your API Gateway at port 3000 to enable live inference.`,
        engine: selectedEngine.id,
        tokens: Math.floor(Math.random() * 80) + 20,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setIsStreaming(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }, 1200);
  }, [input, isStreaming, selectedEngine]);

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.role === "user";
    return (
      <View style={[styles.msgRow, isUser && styles.msgRowUser]}>
        {!isUser && (
          <View style={[styles.avatar, { backgroundColor: colors.primary }]}>
            <Text style={styles.avatarText}>AI</Text>
          </View>
        )}
        <View
          style={[
            styles.bubble,
            isUser
              ? [styles.bubbleUser, { backgroundColor: colors.primary }]
              : [styles.bubbleAssistant, { backgroundColor: colors.surface, borderColor: colors.border }],
          ]}
        >
          <Text style={[styles.bubbleText, { color: isUser ? "#fff" : colors.foreground }]}>
            {item.content}
          </Text>
          {item.tokens && (
            <Text style={[styles.tokenCount, { color: isUser ? "rgba(255,255,255,0.7)" : colors.muted }]}>
              {item.tokens} tokens
            </Text>
          )}
        </View>
      </View>
    );
  };

  return (
    <ScreenContainer containerClassName="bg-background">
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: colors.border, backgroundColor: colors.background }]}>
        <View>
          <Text style={[styles.headerTitle, { color: colors.foreground }]}>AI Inference</Text>
          <Text style={[styles.headerSub, { color: colors.muted }]}>eco-base · port 8001</Text>
        </View>
        {/* Engine selector button */}
        <TouchableOpacity
          style={[styles.engineBadge, { backgroundColor: colors.surface, borderColor: colors.border }]}
          onPress={() => setEnginePickerVisible(true)}
        >
          <View style={[styles.statusDot, { backgroundColor: STATUS_COLOR[selectedEngine.status] }]} />
          <Text style={[styles.engineBadgeText, { color: colors.foreground }]}>{selectedEngine.name}</Text>
          <IconSymbol name="chevron.right" size={14} color={colors.muted} />
        </TouchableOpacity>
      </View>

      {/* Message list */}
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderMessage}
        contentContainerStyle={styles.messageList}
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: false })}
      />

      {/* Streaming indicator */}
      {isStreaming && (
        <View style={[styles.streamingRow, { backgroundColor: colors.surface }]}>
          <ActivityIndicator size="small" color={colors.primary} />
          <Text style={[styles.streamingText, { color: colors.muted }]}>
            {selectedEngine.name} is generating...
          </Text>
        </View>
      )}

      {/* Input bar */}
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <View style={[styles.inputBar, { backgroundColor: colors.surface, borderTopColor: colors.border }]}>
          <TextInput
            style={[styles.input, { color: colors.foreground, backgroundColor: colors.background, borderColor: colors.border }]}
            value={input}
            onChangeText={setInput}
            placeholder="Message eco-base AI..."
            placeholderTextColor={colors.muted}
            multiline
            maxLength={2000}
            returnKeyType="send"
            onSubmitEditing={sendMessage}
          />
          <TouchableOpacity
            style={[styles.sendBtn, { backgroundColor: input.trim() ? colors.primary : colors.border }]}
            onPress={sendMessage}
            disabled={!input.trim() || isStreaming}
          >
            <IconSymbol name="paperplane.fill" size={18} color="#fff" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>

      {/* Engine picker modal */}
      <Modal
        visible={enginePickerVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setEnginePickerVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalSheet, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: colors.foreground }]}>Select Engine</Text>
              <TouchableOpacity onPress={() => setEnginePickerVisible(false)}>
                <IconSymbol name="xmark" size={22} color={colors.muted} />
              </TouchableOpacity>
            </View>
            <FlatList
              data={ENGINES}
              keyExtractor={(e) => e.id}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={[
                    styles.engineRow,
                    { borderBottomColor: colors.border },
                    selectedEngine.id === item.id && { backgroundColor: colors.surface },
                  ]}
                  onPress={() => {
                    setSelectedEngine(item);
                    setEnginePickerVisible(false);
                  }}
                >
                  <View style={[styles.statusDot, { backgroundColor: STATUS_COLOR[item.status] }]} />
                  <View style={styles.engineInfo}>
                    <Text style={[styles.engineName, { color: colors.foreground }]}>{item.name}</Text>
                    <Text style={[styles.engineDesc, { color: colors.muted }]}>{item.description}</Text>
                  </View>
                  <Text style={[styles.enginePort, { color: colors.muted }]}>:{item.port}</Text>
                  {selectedEngine.id === item.id && (
                    <IconSymbol name="checkmark" size={16} color={colors.primary} />
                  )}
                </TouchableOpacity>
              )}
            />
          </View>
        </View>
      </Modal>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 0.5,
  },
  headerTitle: { fontSize: 18, fontWeight: "700" },
  headerSub: { fontSize: 11, marginTop: 1 },
  engineBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
  },
  engineBadgeText: { fontSize: 13, fontWeight: "600" },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  messageList: { padding: 16, gap: 12 },
  msgRow: { flexDirection: "row", alignItems: "flex-end", gap: 8, marginBottom: 8 },
  msgRowUser: { flexDirection: "row-reverse" },
  avatar: { width: 30, height: 30, borderRadius: 15, alignItems: "center", justifyContent: "center" },
  avatarText: { color: "#fff", fontSize: 11, fontWeight: "700" },
  bubble: { maxWidth: "80%", borderRadius: 16, padding: 12, borderWidth: 1 },
  bubbleUser: { borderRadius: 16, borderTopRightRadius: 4, borderWidth: 0 },
  bubbleAssistant: { borderRadius: 16, borderTopLeftRadius: 4 },
  bubbleText: { fontSize: 14, lineHeight: 20 },
  tokenCount: { fontSize: 10, marginTop: 4 },
  streamingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  streamingText: { fontSize: 12 },
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    padding: 12,
    borderTopWidth: 0.5,
  },
  input: {
    flex: 1,
    borderRadius: 20,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 8,
    fontSize: 14,
    maxHeight: 100,
  },
  sendBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "flex-end",
  },
  modalSheet: {
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    borderWidth: 1,
    maxHeight: "75%",
  },
  modalHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 16,
    borderBottomWidth: 0.5,
  },
  modalTitle: { fontSize: 17, fontWeight: "700" },
  engineRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 0.5,
  },
  engineInfo: { flex: 1 },
  engineName: { fontSize: 15, fontWeight: "600" },
  engineDesc: { fontSize: 12, marginTop: 2 },
  enginePort: { fontSize: 12, fontFamily: Platform.OS === "ios" ? "Menlo" : "monospace" },
});
