//
//  OrganizedCategoryViewModel.swift
//  Optimized category loading using server-side organization
//
//  This demonstrates the recommended approach for real-world apps
//  Created by Hesamoddin Saeedi on 1/24/25.
//

import SwiftUI

// MARK: - Optimized Data Models

struct OrganizedCategoriesResponse: Codable {
    let success: Bool
    let categories: OrganizedCategories
    let summary: CategorySummary
}

struct OrganizedCategories: Codable {
    let men: [SimpleCategory]
    let women: [SimpleCategory]
    let unisex: [SimpleCategory]
    let general: [SimpleCategory]
}

struct SimpleCategory: Codable, Identifiable {
    let id: Int
    let name: String
    let label: String
    let productCount: Int
    let parentName: String?
    let parentId: Int?
    let gender: String?
    let section: String
    
    enum CodingKeys: String, CodingKey {
        case id, name, label, gender, section
        case productCount = "product_count"
        case parentName = "parent_name"
        case parentId = "parent_id"
    }
}

struct CategorySummary: Codable {
    let menCount: Int
    let womenCount: Int
    let unisexCount: Int
    let generalCount: Int
    let totalCategories: Int
    
    enum CodingKeys: String, CodingKey {
        case menCount = "men_count"
        case womenCount = "women_count"
        case unisexCount = "unisex_count"
        case generalCount = "general_count"
        case totalCategories = "total_categories"
    }
}

// MARK: - Optimized ViewModel

class OrganizedCategoryViewModel: ObservableObject {
    
    // Pre-organized sections - no processing needed!
    @Published var menCategories: [SimpleCategory] = []
    @Published var womenCategories: [SimpleCategory] = []
    @Published var unisexCategories: [SimpleCategory] = []
    @Published var generalCategories: [SimpleCategory] = []
    
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var summary: CategorySummary?
    
    private let baseURL = "http://127.0.0.1:8000/shop"
    
    init() {
        Task {
            await loadOrganizedCategories()
        }
    }
    
    func loadOrganizedCategories() async {
        await MainActor.run { 
            isLoading = true
            errorMessage = nil
        }
        
        do {
            let urlString = "\(baseURL)/api/organized-categories/"
            guard let url = URL(string: urlString) else {
                await MainActor.run {
                    errorMessage = "Invalid URL"
                    isLoading = false
                }
                return
            }
            
            let (data, _) = try await URLSession.shared.data(from: url)
            let response = try JSONDecoder().decode(OrganizedCategoriesResponse.self, from: data)
            
            await MainActor.run {
                // Direct assignment - no processing needed!
                self.menCategories = response.categories.men
                self.womenCategories = response.categories.women
                self.unisexCategories = response.categories.unisex
                self.generalCategories = response.categories.general
                self.summary = response.summary
                self.isLoading = false
            }
            
        } catch {
            print("Error loading organized categories: \(error)")
            await MainActor.run {
                errorMessage = "Failed to load categories: \(error.localizedDescription)"
                isLoading = false
            }
        }
    }
    
    // MARK: - Helper Methods
    
    func getCategoryById(_ id: Int) -> SimpleCategory? {
        return menCategories.first { $0.id == id } ??
               womenCategories.first { $0.id == id } ??
               unisexCategories.first { $0.id == id } ??
               generalCategories.first { $0.id == id }
    }
    
    func getCategoriesForSection(_ section: String) -> [SimpleCategory] {
        switch section {
        case "men": return menCategories
        case "women": return womenCategories
        case "unisex": return unisexCategories
        case "general": return generalCategories
        default: return []
        }
    }
    
    func getTotalProductCount() -> Int {
        return menCategories.reduce(0) { $0 + $1.productCount } +
               womenCategories.reduce(0) { $0 + $1.productCount } +
               unisexCategories.reduce(0) { $0 + $1.productCount } +
               generalCategories.reduce(0) { $0 + $1.productCount }
    }
}

// MARK: - Optimized UI Implementation

struct OrganizedCategoryView: View {
    @StateObject private var viewModel = OrganizedCategoryViewModel()
    
    var body: some View {
        NavigationView {
            Group {
                if viewModel.isLoading {
                    LoadingView()
                } else if let error = viewModel.errorMessage {
                    ErrorView(message: error) {
                        Task {
                            await viewModel.loadOrganizedCategories()
                        }
                    }
                } else {
                    categorySections
                }
            }
            .navigationTitle("Categories")
            .refreshable {
                await viewModel.loadOrganizedCategories()
            }
        }
    }
    
    private var categorySections: some View {
        ScrollView {
            LazyVStack(spacing: 24) {
                
                // Men's Section
                if !viewModel.menCategories.isEmpty {
                    CategorySectionView(
                        title: "Men's Categories",
                        categories: viewModel.menCategories,
                        color: .blue
                    )
                }
                
                // Women's Section
                if !viewModel.womenCategories.isEmpty {
                    CategorySectionView(
                        title: "Women's Categories", 
                        categories: viewModel.womenCategories,
                        color: .pink
                    )
                }
                
                // Unisex Section
                if !viewModel.unisexCategories.isEmpty {
                    CategorySectionView(
                        title: "Unisex Categories",
                        categories: viewModel.unisexCategories,
                        color: .purple
                    )
                }
                
                // General Section
                if !viewModel.generalCategories.isEmpty {
                    CategorySectionView(
                        title: "Other Categories",
                        categories: viewModel.generalCategories,
                        color: .gray
                    )
                }
                
                // Summary
                if let summary = viewModel.summary {
                    CategorySummaryView(summary: summary)
                }
            }
            .padding()
        }
    }
}

struct CategorySectionView: View {
    let title: String
    let categories: [SimpleCategory]
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(color)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 12) {
                ForEach(categories) { category in
                    SimpleCategoryCard(category: category, color: color) {
                        // Handle category selection
                        loadProductsForCategory(category)
                    }
                }
            }
        }
    }
    
    private func loadProductsForCategory(_ category: SimpleCategory) {
        // Load products using the unified API
        // /api/products/unified/?category_id=\(category.id)
        print("Loading products for: \(category.label)")
    }
}

struct SimpleCategoryCard: View {
    let category: SimpleCategory
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                // Category icon or image
                Circle()
                    .fill(color.opacity(0.2))
                    .frame(width: 60, height: 60)
                    .overlay(
                        Image(systemName: iconForCategory(category.name))
                            .font(.title2)
                            .foregroundColor(color)
                    )
                
                // Category info
                VStack(spacing: 4) {
                    Text(category.label)
                        .font(.caption)
                        .fontWeight(.medium)
                        .multilineTextAlignment(.center)
                        .lineLimit(2)
                    
                    Text("\(category.productCount) products")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            .padding(12)
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(radius: 2)
        }
        .buttonStyle(PlainButtonStyle())
    }
    
    private func iconForCategory(_ name: String) -> String {
        // Map category names to SF Symbols
        let lowercased = name.lowercased()
        if lowercased.contains("ساعت") || lowercased.contains("watch") {
            return "clock"
        } else if lowercased.contains("لباس") || lowercased.contains("clothing") {
            return "tshirt"
        } else if lowercased.contains("عطر") || lowercased.contains("perfume") {
            return "drop"
        } else if lowercased.contains("کفش") || lowercased.contains("shoe") {
            return "shoe"
        } else if lowercased.contains("کتاب") || lowercased.contains("book") {
            return "book"
        } else {
            return "cube.box"
        }
    }
}

struct CategorySummaryView: View {
    let summary: CategorySummary
    
    var body: some View {
        VStack(spacing: 8) {
            Text("Category Summary")
                .font(.headline)
            
            HStack(spacing: 16) {
                SummaryItem(title: "Men", count: summary.menCount, color: .blue)
                SummaryItem(title: "Women", count: summary.womenCount, color: .pink)
                SummaryItem(title: "Unisex", count: summary.unisexCount, color: .purple)
                SummaryItem(title: "General", count: summary.generalCount, color: .gray)
            }
            
            Text("Total: \(summary.totalCategories) categories")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

struct SummaryItem: View {
    let title: String
    let count: Int
    let color: Color
    
    var body: some View {
        VStack(spacing: 4) {
            Text("\(count)")
                .font(.title3)
                .fontWeight(.bold)
                .foregroundColor(color)
            
            Text(title)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
    }
}

struct LoadingView: View {
    var body: some View {
        VStack {
            ProgressView()
                .scaleEffect(1.5)
            Text("Loading categories...")
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.top)
        }
    }
}

struct ErrorView: View {
    let message: String
    let retryAction: () -> Void
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.largeTitle)
                .foregroundColor(.orange)
            
            Text("Error")
                .font(.headline)
            
            Text(message)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            Button("Retry") {
                retryAction()
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
}

// MARK: - Preview

#Preview {
    OrganizedCategoryView()
} 