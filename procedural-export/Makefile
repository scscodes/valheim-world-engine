.PHONY: help build clean test

help:
	@echo "VWE Procedural Export - Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  build    - Build VWE_ProceduralMetadata plugin"
	@echo "  clean    - Remove build artifacts"
	@echo "  test     - Build and show output location"
	@echo "  help     - Show this help message"

build:
	@echo "Building VWE_ProceduralMetadata plugin..."
	cd src/VWE_ProceduralMetadata && dotnet build -c Release
	@echo ""
	@echo "Plugin built:"
	@ls -lh plugins/VWE_ProceduralMetadata.dll 2>/dev/null || echo "Build failed - check errors above"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf src/VWE_ProceduralMetadata/bin/
	rm -rf src/VWE_ProceduralMetadata/obj/
	rm -f plugins/VWE_ProceduralMetadata.dll
	rm -f plugins/VWE_ProceduralMetadata.pdb
	@echo "Clean complete"

test: build
	@echo ""
	@echo "Build successful!"
	@echo "Plugin location: plugins/VWE_ProceduralMetadata.dll"
	@echo ""
	@echo "To test:"
	@echo "  1. Copy plugin to BepInEx container"
	@echo "  2. Run container and check logs for '★★★ ProceduralMetadata'"
	@echo "  3. Check output/metadata/ for JSON export"
