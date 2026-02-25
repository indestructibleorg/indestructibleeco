// @GL-governed
// @GL-layer: GL10-29
// @GL-semantic: esync-platform-source
// @GL-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
//
// GL Unified Charter Activated
/**
 * @GL-governed
 * @GL-layer: esync-platform
 * @GL-semantic: syncd-daemon
 * @GL-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
 *
 * GL Unified Charter Activated
 * SyncD - Core Sync Service Daemon
 */

package main

import (
	"context"
	"flag"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"
)

var (
	version = flag.Bool("version", false, "Show version information")
)

const (
	appName    = "esync-platform-syncd"
	appVersion = "1.0.0"
)

func main() {
	flag.Parse()

	if *version {
		log.Printf("%s v%s", appName, appVersion)
		os.Exit(0)
	}

	log.Printf("Starting %s v%s", appName, appVersion)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	log.Println("Shutting down gracefully...")
	cancel()
	time.Sleep(2 * time.Second)
	log.Println("Shutdown complete")
}
