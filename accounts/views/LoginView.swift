import SwiftUI

struct LoginView: View {
    @State private var first_name = ""
    @State private var password = ""
    @State private var isLoggedIn = false

    var body: some View {
        GeometryReader { geo in
            VStack {
                Text("ورود به سایت")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .padding(.bottom, 20)

                MyToggleNormal2(text: $first_name,  selectedTab1: false,width:geo.size.width/1.2,height:geo.size.height/14, placeholder: "آدرس ایمیل", textAlign: .trailing)
                    .overlay {
                        RoundedRectangle(cornerRadius: 10).stroke(style: StrokeStyle(lineWidth: 1))
                            .fill(Color(#colorLiteral(red: 0.8039215803, green: 0.8039215803, blue: 0.8039215803, alpha: 1)))
                    }
                    .frame(maxWidth: .infinity, alignment: .trailing)
                
                Text("آدرس ایمیل جهت ارسال لینک فعال سازی")
                    .font(.caption)
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity, alignment: .trailing)

                TextField("رمز عبور", text: $password)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .padding(.horizontal, 20)
                    .padding(.top, 20)

                Button("ورود") {
                    // Handle login
                }
                .buttonStyle(CustomButtonStyle())
                .padding(.top, 20)
            }
            .padding()
        }
    }
}

struct LoginView_Previews: PreviewProvider {
    static var previews: some View {
        LoginView()
    }
}

struct CustomButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color.blue)
            .foregroundColor(.white)
            .cornerRadius(10)
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
    }
} 